"""One process-owned composition for QMA mission and task execution services."""

from __future__ import annotations

from dataclasses import dataclass

from qma.daemon.backtest.service import BacktestingService
from qma.daemon.envs.jobs import JobHandleService
from qma.daemon.envs.registry import ExecutionEnvironmentRegistry
from qma.daemon.envs.router import ComputeRouter
from qma.daemon.envs.runtime import RuntimeService
from qma.daemon.journal.authoritative import AuthoritativeJournal
from qma.daemon.journal.variables import GovernedVariableRegistry
from qma.daemon.ledgers.task import TaskLedgerStore
from qma.daemon.sessions.product_session import ProductSessionService
from qma.daemon.taskgraph.compiler import MissionCompiler
from qma.daemon.taskgraph.dispatcher import TaskGraphDispatcher
from qma.daemon.taskgraph.nested import NestedMissionHost
from qma.daemon.taskgraph.projection import TaskGraphStateService
from qma.daemon.tools.registry import ToolRegistry
from qmf.data.store import AppendStore


@dataclass(slots=True)
class DaemonRuntimeComposition:
    """Shared runtime objects; one authority and one identity per process."""

    environments: ExecutionEnvironmentRegistry
    router: ComputeRouter
    task_ledgers: TaskLedgerStore
    dispatcher: TaskGraphDispatcher
    jobs: JobHandleService
    tools: ToolRegistry
    backtesting: BacktestingService
    runtime_service: RuntimeService
    nested_missions: NestedMissionHost
    variables: GovernedVariableRegistry

    @classmethod
    def create(
        cls,
        *,
        journal: AuthoritativeJournal,
        task_graphs: TaskGraphStateService,
        variables: GovernedVariableRegistry,
        compiler: MissionCompiler,
        product_sessions: ProductSessionService | None = None,
        artifact_store: AppendStore | None = None,
    ) -> DaemonRuntimeComposition:
        """Wire existing services around shared durable graph and routing state."""
        environments = ExecutionEnvironmentRegistry()
        router = ComputeRouter(environments=environments)
        task_ledgers = TaskLedgerStore(_journal=journal)
        dispatcher = TaskGraphDispatcher(
            durable=task_graphs,
            environments=environments,
            router=router,
            ledgers=task_ledgers,
        )
        jobs = JobHandleService(router=router, dispatcher=dispatcher, durable=task_graphs)
        tools = ToolRegistry(environments=environments)
        backtesting = BacktestingService(
            tools=tools,
            jobs=jobs,
            environments=environments,
            artifact_store=artifact_store,
        )
        runtime_service = RuntimeService(
            jobs=jobs,
            tools=tools,
            variables=variables,
            environments=environments,
            router=router,
        )
        if product_sessions is not None:
            backtesting.bind_product_sessions(product_sessions)
        nested_missions = NestedMissionHost(
            compiler=compiler,
            jobs=jobs,
            graphs=task_graphs,
            variables=variables,
        )
        return cls(
            environments=environments,
            router=router,
            task_ledgers=task_ledgers,
            dispatcher=dispatcher,
            jobs=jobs,
            tools=tools,
            backtesting=backtesting,
            runtime_service=runtime_service,
            nested_missions=nested_missions,
            variables=variables,
        )

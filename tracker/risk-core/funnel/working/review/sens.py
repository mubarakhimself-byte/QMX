"""Sensitivity of stack_sim: an oracle e-meter (one lambda set to the true optimum), and the picks without the e-bars.
Run: python -I sens.py   (imports stack_sim from this folder by path)"""
import sys,random,importlib.util
sys.argv=["stack_sim","200","120","1","10","none"]
spec=importlib.util.spec_from_file_location("stack_sim",__file__.replace("sens.py","stack_sim.py"))
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
def show(title,edge,flags_list,grid=None):
    if grid: m.GRID[:]=grid
    m.table(title,lambda d:edge,edge,10,flags_list)
base=[("CORE","RCBD"),("all picks, no e-bars","RCBDHLPMK"),("no e-bars, no level drop","RCBDHPMK"),("all picks","RCBDEHLPMK")]
show("HEALTHY +0.10R, mixture e-meter",0.10,base,[0.02,0.04,0.08,0.16,0.32])
show("WEAK +0.05R, mixture e-meter",0.05,base,[0.02,0.04,0.08,0.16,0.32])
show("HEALTHY +0.10R, oracle e-meter",0.10,[("all picks","RCBDEHLPMK")],[0.135])
show("WEAK +0.05R, oracle e-meter",0.05,[("all picks","RCBDEHLPMK")],[0.0675])

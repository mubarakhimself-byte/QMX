"""Copies of his QMX folder's data on This PC and in places he names, and the way back to one
(design 62 C, phase 2). Standard library only.

The words, as he reads them:

- **Backup.** Keeping copies of his QMX folder's data so he can go back to one.
- **Copy.** One dated moment of his data in one backup place, picked by date. Code and disk call
  it a snapshot (`snapshots/<stamp>/`).
- **Quick undo.** The copies in `backups/quick/` on the folder's own drive, every hour. They undo
  a bad edit or a bad upgrade and do not survive a dead disk.
- **Target.** A backup place outside the folder that he named and that holds copies: a folder on
  another drive (the second drive) or, later, an rclone remote (off-site).
- **Proposal.** The second drive QMX suggests. It is not a target until he accepts it.
- **Round.** One pass that makes a copy and sends it to every place that is due.
- **Pool.** The files a place holds once each, by sha256, which every copy's manifest names.
- **Carry on.** His choice that lets this folder keep sending to a place another folder wrote to.
- **Pre-change copy.** The copy of the one store an upgrade changes, kept in `backups/pre-*`.
  QMX's own safety net, not a copy he restores.

`plan` reads `[backup]`, `snapshot` makes one copy, `repository` is a place on disk, `keep` says
which copies a place keeps, and `round` runs one round.
"""

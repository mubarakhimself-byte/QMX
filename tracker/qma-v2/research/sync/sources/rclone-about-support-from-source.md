<!-- Sources (Go source files, read 2026-10-28):
     https://raw.githubusercontent.com/rclone/rclone/master/backend/s3/s3.go
     https://raw.githubusercontent.com/rclone/rclone/master/backend/drive/drive.go
     https://raw.githubusercontent.com/rclone/rclone/master/backend/sftp/sftp.go
     Method: searched each file for the line `func (f *Fs) About(` (the method that reports quota/free space). -->

| Backend file | Has `func (f *Fs) About(` | Line |
|---|---|---|
| backend/s3/s3.go (S3 and S3-compatible, incl. Cloudflare R2) | no match | - |
| backend/drive/drive.go (Google Drive) | yes | 3047 |
| backend/sftp/sftp.go (SFTP, e.g. his server or a storage box) | yes | 2287 |

Combined with rclone-overview.md ("Backends without about capability cannot determine free space for an
rclone mount, or use policy `mfs` (most free space) as a member of an rclone union remote."), an S3/R2 member
cannot take part in the free-space union policies.

<!-- Source: https://raw.githubusercontent.com/rclone/rclone/master/docs/content/s3.md
     Fetched: 2026-10-28. Excerpt: the 'Cloudflare R2' section only (lines 5656-5769), verbatim. -->

### Cloudflare R2 {#cloudflare-r2}

[Cloudflare R2](https://blog.cloudflare.com/r2-open-beta/) Storage
allows developers to store large amounts of unstructured data without
the costly egress bandwidth fees associated with typical cloud storage
services.

Here is an example of making a Cloudflare R2 configuration. First run:

```console
rclone config
```

This will guide you through an interactive setup process.

Note that all buckets are private, and all are stored in the same
"auto" region. It is necessary to use Cloudflare workers to share the
content of a bucket publicly.

```text
No remotes found, make a new one\?
n) New remote
s) Set configuration password
q) Quit config
n/s/q> n
name> r2
Option Storage.
Type of storage to configure.
Choose a number from below, or type in your own value.
...
XX / Amazon S3 Compliant Storage Providers including AWS, Alibaba, Ceph, China Mobile, Cloudflare, ArvanCloud, DigitalOcean, Dreamhost, Huawei OBS, IBM COS, Lyve Cloud, Minio, Magalu, Netease, RackCorp, Scaleway, SeaweedFS, Storj, Synology, Tencent COS and Wasabi
   \ (s3)
...
Storage> s3
Option provider.
Choose your S3 provider.
Choose a number from below, or type in your own value.
Press Enter to leave empty.
...
XX / Cloudflare R2 Storage
   \ (Cloudflare)
...
provider> Cloudflare
Option env_auth.
Get AWS credentials from runtime (environment variables or EC2/ECS meta data if no env vars).
Only applies if access_key_id and secret_access_key is blank.
Choose a number from below, or type in your own boolean value (true or false).
Press Enter for the default (false).
 1 / Enter AWS credentials in the next step.
   \ (false)
 2 / Get AWS credentials from the environment (env vars or IAM).
   \ (true)
env_auth> 1
Option access_key_id.
AWS Access Key ID.
Leave blank for anonymous access or runtime credentials.
Enter a value. Press Enter to leave empty.
access_key_id> ACCESS_KEY
Option secret_access_key.
AWS Secret Access Key (password).
Leave blank for anonymous access or runtime credentials.
Enter a value. Press Enter to leave empty.
secret_access_key> SECRET_ACCESS_KEY
Option region.
Region to connect to.
Choose a number from below, or type in your own value.
Press Enter to leave empty.
 1 / R2 buckets are automatically distributed across Cloudflare's data centers for low latency.
   \ (auto)
region> 1
Option endpoint.
Endpoint for S3 API.
Required when using an S3 clone.
Enter a value. Press Enter to leave empty.
endpoint> https://ACCOUNT_ID.r2.cloudflarestorage.com
Edit advanced config?
y) Yes
n) No (default)
y/n> n
--------------------
y) Yes this is OK (default)
e) Edit this remote
d) Delete this remote
y/e/d> y
```

This will leave your config looking something like:

```ini
[r2]
type = s3
provider = Cloudflare
access_key_id = ACCESS_KEY
secret_access_key = SECRET_ACCESS_KEY
region = auto
endpoint = https://ACCOUNT_ID.r2.cloudflarestorage.com
acl = private
```

Now run `rclone lsf r2:` to see your buckets and `rclone lsf
r2:bucket` to look within a bucket.

For R2 tokens with the "Object Read & Write" permission, you may also
need to add `no_check_bucket = true` for object uploads to work
correctly.

Note that Cloudflare decompresses files uploaded with
`Content-Encoding: gzip` by default which is a deviation from what AWS
does. If this is causing a problem then upload the files with
`--header-upload "Cache-Control: no-transform"`

A consequence of this is that `Content-Encoding: gzip` will never
appear in the metadata on Cloudflare.


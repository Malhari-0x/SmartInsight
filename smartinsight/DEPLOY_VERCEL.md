# Deploy SmartInsight on Vercel

## Files added

- `vercel.json`
- `build_files.sh`
- `runtime.txt`
- `.vercelignore`

## Required env vars in Vercel

- `SECRET_KEY` = long random secret
- `DEBUG` = `False`
- `DATABASE_URL` = Postgres connection string (recommended)

## Optional env vars

- `ALLOWED_HOSTS` = `yourdomain.com,www.yourdomain.com`
- `CSRF_TRUSTED_ORIGINS` = `https://yourdomain.com,https://www.yourdomain.com`

## Important notes

- For production, use Postgres (`DATABASE_URL`) because Vercel filesystem is ephemeral and SQLite is not suitable for writes.
- Uploaded files in `media/` are also ephemeral on Vercel. For stable uploads, use cloud storage (S3/Cloudinary/etc).

## Deploy steps

1. Push code to GitHub.
2. Import repo in Vercel.
3. Add environment variables.
4. Deploy.

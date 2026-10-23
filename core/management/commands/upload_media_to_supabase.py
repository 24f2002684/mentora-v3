import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile


class Command(BaseCommand):
    help = "Uploads existing local media files (avatars, vision boards, task attachments) to the configured Supabase Storage bucket."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='List local media files that would be uploaded without uploading them.'
        )
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Re-upload and overwrite files even if they already exist in the bucket.'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        overwrite = options['overwrite']
        media_root = Path(settings.MEDIA_ROOT)

        self.stdout.write(self.style.NOTICE("=== Mentora Supabase Media Migration ==="))
        self.stdout.write(f"Local Media Directory: {media_root.resolve()}")
        self.stdout.write(f"Storage Backend: {settings.STORAGES['default']['BACKEND']}")

        if not media_root.exists():
            self.stdout.write(self.style.WARNING(f"Local media directory does not exist: {media_root}. No files to migrate."))
            return

        # Find all files recursively
        local_files = []
        for root, _, files in os.walk(media_root):
            for f in files:
                full_path = Path(root) / f
                rel_path = full_path.relative_to(media_root).as_posix()
                local_files.append((full_path, rel_path))

        if not local_files:
            self.stdout.write(self.style.SUCCESS("No local media files found in media root. Nothing to upload."))
            return

        self.stdout.write(f"Discovered {len(local_files)} local media file(s).")

        uploaded_count = 0
        skipped_count = 0

        for full_path, rel_path in local_files:
            size_kb = full_path.stat().st_size / 1024

            if dry_run:
                self.stdout.write(f"  [DRY RUN] Would upload: {rel_path} ({size_kb:.1f} KB)")
                uploaded_count += 1
                continue

            # Check if file already exists in default_storage
            if default_storage.exists(rel_path) and not overwrite:
                self.stdout.write(f"  [SKIP] Already exists in bucket: {rel_path}")
                skipped_count += 1
                continue

            try:
                with open(full_path, 'rb') as f_in:
                    content = f_in.read()
                    default_storage.save(rel_path, ContentFile(content))
                self.stdout.write(self.style.SUCCESS(f"  [UPLOADED] {rel_path} ({size_kb:.1f} KB)"))
                uploaded_count += 1
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"  [ERROR] Failed to upload {rel_path}: {e}"))

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"\nDry run complete. {uploaded_count} file(s) would be uploaded."))
        else:
            self.stdout.write(self.style.SUCCESS(f"\nMigration complete. {uploaded_count} uploaded, {skipped_count} skipped."))

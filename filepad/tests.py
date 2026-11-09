from django.test import TestCase

from filepad.models import UserSpace, UploadedFile, user_directory_path


class UserSpaceModelTests(TestCase):

    def setUp(self):
        self.user_space = UserSpace.objects.create(
            lookup_id="test-lookup-id",
            password_verifier="test-password-verifier"
        )

    def test_vault_uuid_is_generated(self):
        self.assertIsNotNone(self.user_space.vault_uuid)

    def test_each_vault_has_a_unique_uuid(self):
        another_vault = UserSpace.objects.create(
            lookup_id="another-lookup-id",
            password_verifier="another-password-verifier"
        )

        self.assertNotEqual(
            self.user_space.vault_uuid,
            another_vault.vault_uuid
        )

    def test_file_upload_path_uses_vault_uuid(self):
        uploaded_file = UploadedFile(
            user_space=self.user_space
        )

        path = user_directory_path(uploaded_file, "document.pdf")

        expected_path = (
            f"filepad/{self.user_space.vault_uuid}/document.pdf"
        )

        self.assertEqual(path, expected_path)

    def test_deleting_vault_deletes_file_metadata(self):
        uploaded_file = UploadedFile.objects.create(
            user_space=self.user_space,
            file="filepad/test/document.pdf",
            original_filename="document.pdf",
            file_size=1024,
            file_type="application/pdf"
        )

        self.assertEqual(self.user_space.files.count(), 1)

        self.user_space.delete()

        self.assertFalse(
            UploadedFile.objects.filter(id=uploaded_file.id).exists()
        )

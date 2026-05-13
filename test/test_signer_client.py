import ctypes
import unittest
from unittest.mock import Mock, patch

import lighter.signer_client as signer_client


class TestSignerClientHelpers(unittest.TestCase):
    def test_decode_and_free_uses_passed_signer(self):
        signer = Mock()
        ptr = ctypes.cast(ctypes.create_string_buffer(b"hello"), ctypes.c_void_p)

        decoded = signer_client.decode_and_free(ptr, signer)

        self.assertEqual(decoded, "hello")
        signer.Free.assert_called_once_with(ptr)

    def test_get_signer_reuses_shared_library(self):
        shared_signer = Mock()

        with patch.object(signer_client, "__signer", None):
            with patch.object(signer_client, "__get_shared_library", return_value=shared_signer) as get_library:
                with patch.object(signer_client, "__populate_shared_library_functions") as populate:
                    first = signer_client.get_signer()
                    second = signer_client.get_signer()

        self.assertIs(first, shared_signer)
        self.assertIs(second, shared_signer)
        get_library.assert_called_once_with()
        populate.assert_called_once_with(shared_signer)

    def test_create_signer_isolated_copies_library_before_loading(self):
        isolated_signer = Mock()
        source_library_path = "/signers/lighter-signer-darwin-arm64.dylib"
        temp_dir = "/tmp/lighter-signer-test"
        isolated_library_path = f"{temp_dir}/lighter-signer-darwin-arm64.dylib"

        with patch.object(signer_client, "__isolated_signer_directories", []):
            with patch.object(signer_client, "__get_shared_library_path", return_value=source_library_path):
                with patch.object(signer_client.tempfile, "mkdtemp", return_value=temp_dir):
                    with patch.object(signer_client.shutil, "copy2") as copy2:
                        with patch.object(signer_client, "__load_shared_library", return_value=isolated_signer) as load_library:
                            with patch.object(signer_client, "__populate_shared_library_functions") as populate:
                                signer = signer_client.create_signer(isolated=True)

        self.assertIs(signer, isolated_signer)
        copy2.assert_called_once_with(source_library_path, isolated_library_path)
        load_library.assert_called_once_with(isolated_library_path)
        populate.assert_called_once_with(isolated_signer)


class TestSignerClientInit(unittest.TestCase):
    def test_init_defaults_to_isolated_signer_instance(self):
        signer = Mock()
        nonce_manager = Mock()

        with patch.object(signer_client, "create_signer", return_value=signer) as create_signer:
            with patch.object(signer_client.lighter, "ApiClient", return_value=Mock()):
                with patch.object(signer_client.lighter, "TransactionApi", return_value=Mock()):
                    with patch.object(signer_client.lighter, "OrderApi", return_value=Mock()):
                        with patch.object(signer_client.nonce_manager, "nonce_manager_factory", return_value=nonce_manager):
                            with patch.object(signer_client.SignerClient, "create_client"):
                                client = signer_client.SignerClient(
                                    url="https://api.testnet.example",
                                    account_index=7,
                                    api_private_keys={3: "abc123"},
                                )

        self.assertIs(client.signer, signer)
        create_signer.assert_called_once_with(isolated=True)

    def test_init_can_request_isolated_signer_instance(self):
        signer = Mock()
        nonce_manager = Mock()

        with patch.object(signer_client, "create_signer", return_value=signer) as create_signer:
            with patch.object(signer_client.lighter, "ApiClient", return_value=Mock()):
                with patch.object(signer_client.lighter, "TransactionApi", return_value=Mock()):
                    with patch.object(signer_client.lighter, "OrderApi", return_value=Mock()):
                        with patch.object(signer_client.nonce_manager, "nonce_manager_factory", return_value=nonce_manager):
                            with patch.object(signer_client.SignerClient, "create_client") as create_client:
                                client = signer_client.SignerClient(
                                    url="https://api.testnet.example",
                                    account_index=7,
                                    api_private_keys={3: "abc123"},
                                    isolated_signer_instance=True,
                                )

        self.assertIs(client.signer, signer)
        create_signer.assert_called_once_with(isolated=True)
        create_client.assert_called_once_with(3)


if __name__ == "__main__":
    unittest.main()

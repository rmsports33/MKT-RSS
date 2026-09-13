#!/usr/bin/env python3
"""
Script de comando para Google Drive via OpenCode
Uso: python drive_command.py <comando> [argumentos]
"""

import sys
import json
from google_drive_client import get_client_from_env


def main():
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python drive_command.py list [pasta_id]")
        print("  python drive_command.py download <file_id> [output_path]")
        print("  python drive_command.py upload <file_path> [pasta_id]")
        print("  python drive_command.py search <termo>")
        print("  python drive_command.py mkdir <nome_pasta>")
        print("  python drive_command.py delete <file_id>")
        print("  python drive_command.py info <file_id>")
        return

    command = sys.argv[1]
    client = get_client_from_env()

    if command == "list":
        folder_id = sys.argv[2] if len(sys.argv) > 2 else None
        files = client.list_files(folder_id=folder_id)
        print(json.dumps(files, indent=2, ensure_ascii=False))

    elif command == "download":
        if len(sys.argv) < 3:
            print("Uso: python drive_command.py download <file_id> [output_path]")
            return
        file_id = sys.argv[2]
        output = sys.argv[3] if len(sys.argv) > 3 else None
        client.download_file(file_id, output)

    elif command == "upload":
        if len(sys.argv) < 3:
            print("Uso: python drive_command.py upload <file_path> [pasta_id]")
            return
        file_path = sys.argv[2]
        folder_id = sys.argv[3] if len(sys.argv) > 3 else None
        client.upload_file(file_path, folder_id)

    elif command == "search":
        if len(sys.argv) < 3:
            print("Uso: python drive_command.py search <termo>")
            return
        term = sys.argv[2]
        results = client.search_files(term)
        print(json.dumps(results, indent=2, ensure_ascii=False))

    elif command == "mkdir":
        if len(sys.argv) < 3:
            print("Uso: python drive_command.py mkdir <nome_pasta>")
            return
        folder_name = sys.argv[2]
        client.create_folder(folder_name)

    elif command == "delete":
        if len(sys.argv) < 3:
            print("Uso: python drive_command.py delete <file_id>")
            return
        file_id = sys.argv[2]
        client.delete_file(file_id)

    elif command == "info":
        if len(sys.argv) < 3:
            print("Uso: python drive_command.py info <file_id>")
            return
        file_id = sys.argv[2]
        info = client.get_file_info(file_id)
        print(json.dumps(info, indent=2, ensure_ascii=False))

    else:
        print(f"Comando desconhecido: {command}")


if __name__ == "__main__":
    main()
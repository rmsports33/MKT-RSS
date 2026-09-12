"""
Cliente Google Drive para OpenCode
Integração completa com API v3 via OAuth 2.0
"""

import os
import io
from pathlib import Path
from typing import Optional, List, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from googleapiclient.errors import HttpError


class GoogleDriveClient:
    """Cliente para operações no Google Drive."""

    SCOPES = ['https://www.googleapis.com/auth/drive']

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_file: str = 'token.json',
        credentials_file: str = 'credentials.json'
    ):
        """
        Inicializa o cliente Google Drive.

        Args:
            client_id: ID do cliente OAuth
            client_secret: Segredo do cliente OAuth
            token_file: Caminho para salvar/carregar o token
            credentials_file: Caminho para o arquivo de credenciais
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_file = token_file
        self.credentials_file = credentials_file
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Realiza a autenticação OAuth 2.0."""
        creds = None

        # Verificar se existe token salvo
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(
                self.token_file,
                self.SCOPES
            )

        # Se não tiver credenciais válidas, fazer login
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # Criar arquivo de credenciais temporário
                creds_data = {
                    "installed": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": ["http://localhost"]
                    }
                }

                import json
                with open(self.credentials_file, 'w') as f:
                    json.dump(creds_data, f)

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, 
                    self.SCOPES
                )
                print("\n[AUTH] Abrindo navegador para autorizacao...")
                print("[AUTH] Se o navegador NAO abrir, copie a URL abaixo e cole no Chrome:\n")
                try:
                    creds = flow.run_local_server(port=0, open_browser=True)
                except Exception as e:
                    print(f"[AUTH] Erro ao abrir servidor local: {e}")
                    print("[AUTH] Tentando modo manual (copie e cole a URL)...")
                    creds = flow.run_local_server(port=0, open_browser=False)
                
                # Limpar arquivo temporário
                if os.path.exists(self.credentials_file):
                    os.remove(self.credentials_file)

            # Salvar token para próxima vez
            with open(self.token_file, 'w') as f:
                f.write(creds.to_json())

        self.service = build('drive', 'v3', credentials=creds)

    def list_files(
        self,
        page_size: int = 10,
        folder_id: Optional[str] = None,
        query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Lista arquivos no Google Drive.

        Args:
            page_size: Número máximo de arquivos por página
            folder_id: ID da pasta (None para raiz)
            query: Consulta de filtro (ex: "name contains 'relatorio'")

        Returns:
            Lista de dicionários com informações dos arquivos
        """
        try:
            q = query or ""
            if folder_id:
                q += f" and '{folder_id}' in parents" if q else f"'{folder_id}' in parents"

            results = self.service.files().list(
                pageSize=page_size,
                fields="nextPageToken, files(id, name, mimeType, size, modifiedTime)",
                q=q if q else None,
                orderBy="modifiedTime desc"
            ).execute()

            return results.get('files', [])

        except HttpError as error:
            print(f'Erro ao listar arquivos: {error}')
            return []

    def download_file(
        self,
        file_id: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        Baixa um arquivo do Google Drive.

        Args:
            file_id: ID do arquivo
            output_path: Caminho de saída (None = nome original)

        Returns:
            Caminho do arquivo baixado
        """
        try:
            # Obter metadados do arquivo
            file = self.service.files().get(
                fileId=file_id,
                fields='name'
            ).execute()

            file_name = file.get('name', 'downloaded_file')
            output_path = output_path or file_name

            # Baixar arquivo
            request = self.service.files().get_media(fileId=file_id)
            fh = io.FileIO(output_path, 'wb')
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    print(f'Progresso: {int(status.progress() * 100)}%')

            print(f'Arquivo baixado: {output_path}')
            return output_path

        except HttpError as error:
            print(f'Erro ao baixar arquivo: {error}')
            return ""

    def upload_file(
        self,
        file_path: str,
        folder_id: Optional[str] = None,
        mime_type: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Envia um arquivo para o Google Drive.

        Args:
            file_path: Caminho local do arquivo
            folder_id: ID da pasta de destino
            mime_type: Tipo MIME (auto-detectado se None)

        Returns:
            Dicionário com id e nome do arquivo enviado
        """
        try:
            file_name = Path(file_path).name

            file_metadata = {'name': file_name}
            if folder_id:
                file_metadata['parents'] = [folder_id]

            # Detectar tipo MIME
            if not mime_type:
                import mimetypes
                mime_type, _ = mimetypes.guess_type(file_path)
                mime_type = mime_type or 'application/octet-stream'

            media = MediaFileUpload(
                file_path,
                mimetype=mime_type,
                resumable=True
            )

            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name'
            ).execute()

            print(f'Arquivo enviado: {file.get("name")} (ID: {file.get("id")})')
            return {'id': file.get('id'), 'name': file.get('name')}

        except HttpError as error:
            print(f'Erro ao enviar arquivo: {error}')
            return {}

    def create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> str:
        """
        Cria uma pasta no Google Drive.

        Args:
            folder_name: Nome da pasta
            parent_id: ID da pasta pai (None = raiz)

        Returns:
            ID da pasta criada
        """
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }

            if parent_id:
                file_metadata['parents'] = [parent_id]

            file = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()

            folder_id = file.get('id')
            print(f'Pasta criada: {folder_name} (ID: {folder_id})')
            return folder_id

        except HttpError as error:
            print(f'Erro ao criar pasta: {error}')
            return ""

    def delete_file(self, file_id: str) -> bool:
        """
        Exclui um arquivo do Google Drive.

        Args:
            file_id: ID do arquivo

        Returns:
            True se excluído com sucesso
        """
        try:
            self.service.files().delete(fileId=file_id).execute()
            print(f'Arquivo excluído: {file_id}')
            return True

        except HttpError as error:
            print(f'Erro ao excluir arquivo: {error}')
            return False

    def search_files(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Busca arquivos por nome.

        Args:
            search_term: Termo de busca

        Returns:
            Lista de arquivos encontrados
        """
        query = f"name contains '{search_term}'"
        return self.list_files(query=query)

    def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """
        Obtém informações detalhadas de um arquivo.

        Args:
            file_id: ID do arquivo

        Returns:
            Dicionário com metadados do arquivo
        """
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields='id, name, mimeType, size, createdTime, modifiedTime, webViewLink'
            ).execute()
            return file

        except HttpError as error:
            print(f'Erro ao obter informações: {error}')
            return {}


def get_client_from_env() -> GoogleDriveClient:
    """
    Cria um cliente usando variáveis de ambiente.

    Variáveis necessárias:
    - GOOGLE_DRIVE_CLIENT_ID
    - GOOGLE_DRIVE_CLIENT_SECRET

    Returns:
        Instância do GoogleDriveClient
    """
    from dotenv import load_dotenv
    load_dotenv()

    client_id = os.getenv('GOOGLE_DRIVE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_DRIVE_CLIENT_SECRET')

    if not client_id or not client_secret:
        raise ValueError(
            "Configure as variáveis de ambiente:\n"
            "  GOOGLE_DRIVE_CLIENT_ID=seu_client_id\n"
            "  GOOGLE_DRIVE_CLIENT_SECRET=seu_client_secret"
        )

    return GoogleDriveClient(client_id=client_id, client_secret=client_secret)
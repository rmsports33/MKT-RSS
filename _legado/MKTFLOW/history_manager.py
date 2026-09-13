class HistoryManager:
    def __init__(self, window_size=4):
        self.window_size = window_size
        self.resumo_acumulado = ""

    def gerenciar_historico(self, system_prompt: str, conversation_history: list, new_user_message: str):
        """
        Gerencia o histórico de conversação, mantendo uma janela recente e um resumo acumulado.
        
        Args:
            system_prompt (str): Prompt do sistema.
            conversation_history (list): Lista de mensagens anteriores.
            new_user_message (str): Nova mensagem do usuário.
        
        Returns:
            tuple: (messages, resumo_acumulado)
        """
        # Mantém apenas a janela recente
        if len(conversation_history) > self.window_size:
            recent_window = conversation_history[-self.window_size:]
            # Aqui poderíamos atualizar o resumo acumulado, mas vamos simplificar
            self.resumo_acumulado = "Histórico resumido (versão simplificada)."
        else:
            recent_window = conversation_history

        # Monta a lista de mensagens
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(recent_window)
        messages.append({"role": "user", "content": new_user_message})
        
        return messages, self.resumo_acumulado
/**
 * Conexo Editorial Gate V1 — JavaScript do novo painel de aprovação.
 * Funcionalidades:
 * - Seleção de artigo na lista (esquerda)
 * - Atualização do preview sem recarregar a página (direita)
 * - Abas: Pré-visualização, Detalhes, Verificação
 * - Decisão editorial: APROVO / DESAPROVO
 * - Motivos de reprovação com seleção múltipla
 * - Justificativa obrigatória para reprovação
 * - Botão SALVAR RESPOSTA com validação e envio via AJAX
 */

(function() {
    'use strict';

    var cxgv1 = {
        currentArticleId: null,
        currentSnapshotHash: null,
        currentArticleData: null,

        // Elementos DOM
        elements: {
            articleList: null,
            previewPanel: null,
            previewImage: null,
            previewTitle: null,
            previewSubtitle: null,
            previewContent: null,
            previewCategory: null,
            previewDate: null,
            previewStatus: null,
            tabs: null,
            tabContents: null,
            approveBtn: null,
            rejectBtn: null,
            rejectReasons: null,
            justificationField: null,
            saveBtn: null,
            saveMessage: null,
            decisionHistory: null,
        },

        init: function() {
            this.cacheElements();
            this.bindEvents();
            this.loadDrafts();
        },

        cacheElements: function() {
            this.elements.articleList = document.getElementById('cxgv1-article-list');
            this.elements.previewPanel = document.getElementById('cxgv1-preview-panel');
            this.elements.previewImage = document.getElementById('cxgv1-preview-image');
            this.elements.previewTitle = document.getElementById('cxgv1-preview-title');
            this.elements.previewSubtitle = document.getElementById('cxgv1-preview-subtitle');
            this.elements.previewContent = document.getElementById('cxgv1-preview-content');
            this.elements.previewCategory = document.getElementById('cxgv1-preview-category');
            this.elements.previewDate = document.getElementById('cxgv1-preview-date');
            this.elements.previewStatus = document.getElementById('cxgv1-preview-status');
            this.elements.tabs = document.querySelectorAll('.cxgv1-tab');
            this.elements.tabContents = document.querySelectorAll('.cxgv1-tab-content');
            this.elements.approveBtn = document.getElementById('cxgv1-btn-approve');
            this.elements.rejectBtn = document.getElementById('cxgv1-btn-reject');
            this.elements.rejectReasons = document.querySelectorAll('input[name="cxgv1-reject-reason"]');
            this.elements.justificationField = document.getElementById('cxgv1-justification');
            this.elements.saveBtn = document.getElementById('cxgv1-btn-save');
            this.elements.saveMessage = document.getElementById('cxgv1-save-message');
            this.elements.decisionHistory = document.getElementById('cxgv1-decision-history');
        },

        bindEvents: function() {
            // Abas
            this.elements.tabs.forEach(function(tab) {
                tab.addEventListener('click', function() {
                    var tabName = this.getAttribute('data-tab');
                    cxgv1.switchTab(tabName);
                });
            });

            // Botões de decisão
            this.elements.approveBtn.addEventListener('click', function() {
                cxgv1.setDecision('approve');
            });

            this.elements.rejectBtn.addEventListener('click', function() {
                cxgv1.setDecision('reject');
            });

            // Justificativa - habilitar/desabilitar botão salvar
            this.elements.justificationField.addEventListener('input', function() {
                cxgv1.updateSaveButtonState();
            });

            // Motivos de reprovação
            this.elements.rejectReasons.forEach(function(radio) {
                radio.addEventListener('change', function() {
                    cxgv1.updateSaveButtonState();
                });
            });

            // Botão salvar
            this.elements.saveBtn.addEventListener('click', function() {
                cxgv1.saveDecision();
            });
        },

        loadDrafts: function() {
            var self = this;
            fetch('?page=cxgv1-drafts&action=list', {
                method: 'GET',
                credentials: 'same-origin',
            })
            .then(function(response) { return response.json(); })
            .then(function(data) {
                if (data.error) {
                    cxgv1.showMessage('Erro ao carregar rascunhos: ' + data.error, 'error');
                    return;
                }
                self.renderDraftList(data.drafts);
            })
            .catch(function(error) {
                cxgv1.showMessage('Erro de rede ao carregar rascunhos.', 'error');
                console.error(error);
            });
        },

        renderDraftList: function(drafts) {
            var list = this.elements.articleList;
            list.innerHTML = '';

            drafts.forEach(function(draft) {
                var item = document.createElement('div');
                item.className = 'cxgv1-article-item';
                if (draft.id === self.currentArticleId) {
                    item.classList.add('selected');
                }

                var thumbnailHtml = draft.thumbnail_url
                    ? '<img src="' + escapeHtml(draft.thumbnail_url) + '" alt="' + escapeHtml(draft.thumbnail_alt) + '" class="cxgv1-thumbnail">'
                    : '<div class="cxgv1-thumbnail-placeholder">Sem imagem</div>';

                var statusClass = 'cxgv1-status-' + draft.status;
                var categoryHtml = draft.categories.map(function(cat) {
                    return '<span class="cxgv1-category">' + escapeHtml(cat) + '</span>';
                }).join('');

                item.innerHTML =
                    '<div class="cxgv1-thumbnail-container">' + thumbnailHtml + '</div>' +
                    '<div class="cxgv1-article-info">' +
                    '<h3 class="cxgv1-article-title" data-id="' + draft.id + '">' + escapeHtml(draft.title) + '</h3>' +
                    '<div class="cxgv1-article-meta">' +
                    '<span class="cxgv1-date">' + formatDate(draft.date) + '</span>' +
                    '<span class="cxgv1-status ' + statusClass + '">' + draft.status + '</span>' +
                    categoryHtml +
                    '</div>' +
                    '</div>';

                item.addEventListener('click', function() {
                    self.selectArticle(draft.id, draft);
                });

                list.appendChild(item);
            });
        },

        selectArticle: function(id, articleData) {
            this.currentArticleId = id;
            this.currentArticleData = articleData;
            this.currentSnapshotHash = articleData.hash || null;

            // Atualizar seleção visual na lista
            var items = document.querySelectorAll('.cxgv1-article-item');
            items.forEach(function(item) {
                item.classList.remove('selected');
            });
            event.currentTarget.classList.add('selected');

            // Carregar detalhes no preview
            this.loadArticleDetail(id);
        },

        loadArticleDetail: function(id) {
            var self = this;
            fetch('?page=cxgv1-drafts&action=detail&id=' + id, {
                method: 'GET',
                credentials: 'same-origin',
            })
            .then(function(response) { return response.json(); })
            .then(function(data) {
                if (data.error) {
                    cxgv1.showMessage('Erro ao carregar detalhes: ' + data.error, 'error');
                    return;
                }
                self.renderPreview(data);
                self.loadDecisionHistory(id);
            })
            .catch(function(error) {
                cxgv1.showMessage('Erro de rede ao carregar detalhes.', 'error');
                console.error(error);
            });
        },

        renderPreview: function(article) {
            // Atualizar conteúdo do preview
            if (article.thumbnail_url) {
                this.elements.previewImage.src = article.thumbnail_url;
                this.elements.previewImage.alt = article.thumbnail_alt || '';
                this.elements.previewImage.style.display = 'block';
            } else {
                this.elements.previewImage.style.display = 'none';
            }

            this.elements.previewTitle.textContent = article.title;
            this.elements.previewSubtitle.textContent = article.subtitle || '';
            this.elements.previewContent.innerHTML = article.content;
            this.elements.previewCategory.textContent = article.categories.join(', ');
            this.elements.previewDate.textContent = formatDate(article.date);
            this.elements.previewStatus.textContent = article.status;

            // Mostrar painel de preview
            this.elements.previewPanel.style.display = 'block';

            // Resetar decisão
            this.resetDecision();
        },

        switchTab: function(tabName) {
            // Atualizar abas
            this.elements.tabs.forEach(function(tab) {
                if (tab.getAttribute('data-tab') === tabName) {
                    tab.classList.add('active');
                    tab.setAttribute('aria-pressed', 'true');
                } else {
                    tab.classList.remove('active');
                    tab.setAttribute('aria-pressed', 'false');
                }
            });

            // Atualizar conteúdos
            this.elements.tabContents.forEach(function(content) {
                if (content.id === 'cxgv1-tab-' + tabName) {
                    content.classList.add('active');
                } else {
                    content.classList.remove('active');
                }
            });
        },

        setDecision: function(decision) {
            // Resetar ambos os botões
            this.elements.approveBtn.classList.remove('selected');
            this.elements.rejectBtn.classList.remove('selected');

            if (decision === 'approve') {
                this.elements.approveBtn.classList.add('selected');
                this.elements.rejectReasons.forEach(function(radio) {
                    radio.disabled = true;
                    radio.checked = false;
                });
                this.elements.justificationField.disabled = true;
                this.elements.justificationField.value = '';
            } else if (decision === 'reject') {
                this.elements.rejectBtn.classList.add('selected');
                this.elements.rejectReasons.forEach(function(radio) {
                    radio.disabled = false;
                });
                this.elements.justificationField.disabled = false;
            }

            this.updateSaveButtonState();
        },

        resetDecision: function() {
            this.elements.approveBtn.classList.remove('selected');
            this.elements.rejectBtn.classList.remove('selected');
            this.elements.rejectReasons.forEach(function(radio) {
                radio.disabled = false;
                radio.checked = false;
            });
            this.elements.justificationField.disabled = false;
            this.elements.justificationField.value = '';
            this.updateSaveButtonState();
        },

        updateSaveButtonState: function() {
            var isApproved = this.elements.approveBtn.classList.contains('selected');
            var isRejected = this.elements.rejectBtn.classList.contains('selected');
            var hasReason = false;
            var hasJustification = false;

            this.elements.rejectReasons.forEach(function(radio) {
                if (radio.checked) {
                    hasReason = true;
                }
            });

            if (this.elements.justificationField.value.trim() !== '') {
                hasJustification = true;
            }

            var canSave = false;
            if (isApproved) {
                canSave = true;
            } else if (isRejected) {
                canSave = hasReason && hasJustification;
            }

            this.elements.saveBtn.disabled = !canSave;
        },

        saveDecision: function() {
            var self = this;
            var decision = this.elements.approveBtn.classList.contains('selected') ? 'approve' : 'reject';
            var rejectionReasons = [];
            var justification = '';

            this.elements.rejectReasons.forEach(function(radio) {
                if (radio.checked) {
                    rejectionReasons.push(radio.value);
                }
            });
            justification = this.elements.justificationField.value.trim();

            if (!this.currentArticleId || !this.currentSnapshotHash) {
                this.showMessage('Nenhum artigo selecionado.', 'error');
                return;
            }

            this.elements.saveBtn.disabled = true;
            this.elements.saveBtn.textContent = 'Salvando...';
            this.hideMessage();

            var formData = new FormData();
            formData.append('action', 'cxgv1_save_decision');
            formData.append('post_id', this.currentArticleId);
            formData.append('decision', decision);
            formData.append('snapshot_hash', this.currentSnapshotHash);
            formData.append('reviewer_id', cxgv1_current_user_id); // Definido pelo PHP
            formData.append('nonce', cxgv1_nonce); // Definido pelo PHP

            if (decision === 'reject') {
                formData.append('rejection_reasons', JSON.stringify(rejectionReasons));
                formData.append('justification', justification);
            }

            fetch(ajaxurl, {
                method: 'POST',
                body: formData,
                credentials: 'same-origin',
            })
            .then(function(response) { return response.json(); })
            .then(function(data) {
                if (data.success) {
                    cxgv1.showMessage(data.message, 'success');
                    cxgv1.elements.saveBtn.textContent = 'Salvo com sucesso!';
                    cxgv1.elements.saveBtn.classList.add('saved');
                    // Recarregar histórico
                    cxgv1.loadDecisionHistory(self.currentArticleId);
                } else {
                    cxgv1.showMessage(data.error || 'Erro ao salvar decisão.', 'error');
                    cxgv1.elements.saveBtn.disabled = false;
                    cxgv1.elements.saveBtn.textContent = 'SALVAR RESPOSTA';
                }
            })
            .catch(function(error) {
                cxgv1.showMessage('Erro de rede ao salvar decisão.', 'error');
                cxgv1.elements.saveBtn.disabled = false;
                cxgv1.elements.saveBtn.textContent = 'SALVAR RESPOSTA';
                console.error(error);
            });
        },

        loadDecisionHistory: function(id) {
            var self = this;
            fetch('?page=cxgv1-drafts&action=history&id=' + id, {
                method: 'GET',
                credentials: 'same-origin',
            })
            .then(function(response) { return response.json(); })
            .then(function(data) {
                if (data.error) {
                    cxgv1.elements.decisionHistory.innerHTML = '<p>Erro ao carregar histórico.</p>';
                    return;
                }
                self.renderDecisionHistory(data.history);
            })
            .catch(function(error) {
                cxgv1.elements.decisionHistory.innerHTML = '<p>Erro de rede ao carregar histórico.</p>';
                console.error(error);
            });
        },

        renderDecisionHistory: function(history) {
            var container = this.elements.decisionHistory;
            container.innerHTML = '';

            if (history.length === 0) {
                container.innerHTML = '<p class="cxgv1-no-history">Nenhuma decisão registrada.</p>';
                return;
            }

            history.forEach(function(item) {
                var entry = document.createElement('div');
                entry.className = 'cxgv1-history-entry';
                var dateStr = new Date(item.reviewed_at * 1000).toLocaleString('pt-BR');
                var decisionClass = item.decision === 'approved' ? 'cxgv1-history-approved' : 'cxgv1-history-rejected';
                var decisionText = item.decision === 'approved' ? 'APROVADO' : 'REPROVADO';

                var reasonsHtml = '';
                if (item.rejection_reasons && item.rejection_reasons.length > 0) {
                    reasonsHtml = '<ul class="cxgv1-reasons">' +
                        item.rejection_reasons.map(function(r) { return '<li>' + escapeHtml(r) + '</li>'; }).join('') +
                        '</ul>';
                }

                var justificationHtml = item.justification
                    ? '<p class="cxgv1-justification"><strong>Justificativa:</strong> ' + escapeHtml(item.justification) + '</p>'
                    : '';

                entry.innerHTML =
                    '<div class="cxgv1-history-decision ' + decisionClass + '">' +
                    '<strong>' + decisionText + '</strong> - ' + dateStr +
                    '</div>' +
                    reasonsHtml +
                    justificationHtml;

                container.appendChild(entry);
            });
        },

        showMessage: function(text, type) {
            var msg = this.elements.saveMessage;
            msg.textContent = text;
            msg.className = 'cxgv1-save-message cxgv1-message-' + type;
            msg.style.display = 'block';

            setTimeout(function() {
                msg.style.display = 'none';
            }, 5000);
        },

        hideMessage: function() {
            this.elements.saveMessage.style.display = 'none';
        },
    };

    // Inicializar quando o DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            cxgv1.init();
        });
    } else {
        cxgv1.init();
    }

    // Funções utilitárias
    function escapeHtml(text) {
        if (!text) return '';
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function formatDate(dateString) {
        if (!dateString) return '';
        var date = new Date(dateString);
        return date.toLocaleDateString('pt-BR') + ' ' + date.toLocaleTimeString('pt-BR', {hour: '2-digit', minute: '2-digit'});
    }

    // Expor cxgv1 globalmente para uso em templates PHP
    window.cxgv1 = cxgv1;

})();

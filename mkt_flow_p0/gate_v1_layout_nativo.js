/**
 * Gate V1 — layout nativo: preview dinâmico e decisão via formulário NATIVO.
 *
 * - Preview usa a rota nativa existente: GET /conexo/v1/editorial/snapshot/{id}
 * - SALVAR RESPOSTA (APROVAR) submete o formulário nativo identificado por ID.
 * - NÃO marca os 13 critérios humanos nem inventa evidências.
 * - NÃO altera `publication_mode` (destino nativo preservado).
 * - Reprovação usa o handler nativo com o nonce nativo.
 */
(function () {
    'use strict';
    var cfg = window.cxgv1nat_cfg || {};
    var root = document.getElementById('cxgv1nat-root');
    if (!root) return;

    var selectedId = parseInt(root.getAttribute('data-post-id'), 10);
    var snapshot = root.getAttribute('data-snapshot');
    var decision = null;

    var el = {
        list: document.getElementById('cxgv1nat-list'),
        detail: document.getElementById('cxgv1nat-detail'),
        approve: document.getElementById('cxgv1nat-approve'),
        reject: document.getElementById('cxgv1nat-reject'),
        reasons: document.getElementById('cxgv1nat-reasons'),
        justWrap: document.getElementById('cxgv1nat-just-wrap'),
        just: document.getElementById('cxgv1nat-just'),
        save: document.getElementById('cxgv1nat-save'),
        msg: document.getElementById('cxgv1nat-msg'),
        tabs: document.querySelectorAll('.cxgv1nat-tab'),
    };

    function showMsg(text, ok) {
        el.msg.textContent = text;
        el.msg.className = 'cxgv1nat-msg ' + (ok ? 'ok' : 'err');
        el.msg.hidden = false;
    }

    // Preview dinâmico via rota NATIVA existente (somente leitura autenticada).
    function preview(id) {
        fetch(cfg.apiBase + '/snapshot/' + id, {
            credentials: 'same-origin',
            headers: { 'X-WP-Nonce': cfg.nonce || '' }
        })
        .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
        .then(function (data) {
            var s = data.snapshot || {};
            snapshot = data.snapshot_sha256 || snapshot;
            el.detail.innerHTML = '<h4>' + esc(s.post_title || '') + '</h4>' +
                '<p class="cxgv1nat-sub2">' + esc(s.post_modified || '') + '</p>' +
                '<div class="cxgv1nat-body">' + (s.post_content || '') + '</div>';
            var pv = document.getElementById('cxgv1nat-tab-preview');
            if (pv) pv.innerHTML = el.detail.innerHTML;
            var det = document.getElementById('cxgv1nat-tab-details');
            if (det) det.innerHTML = '<p>ID: ' + esc(id) + '</p><p>Status: ' + esc(s.post_status || '') + '</p><p>Snapshot: <code>' + esc(snapshot) + '</code></p>';
            resetDecision();
        })
        .catch(function (e) { showMsg('Falha no preview: ' + e.message, false); });
    }

    // Seleção na lista (renderizada no servidor com dados nativos).
    if (el.list) {
        Array.prototype.forEach.call(el.list.querySelectorAll('.cxgv1nat-item'), function (item) {
            item.addEventListener('click', function () {
                Array.prototype.forEach.call(el.list.querySelectorAll('.cxgv1nat-item'), function (c) { c.classList.remove('sel'); });
                item.classList.add('sel');
                selectedId = parseInt(item.getAttribute('data-id'), 10);
                snapshot = item.getAttribute('data-snapshot') || snapshot;
                preview(selectedId);
            });
        });
    }

    function resetDecision() {
        decision = null;
        el.approve.classList.remove('sel');
        el.reject.classList.remove('sel');
        el.reasons.hidden = true;
        el.justWrap.hidden = true;
        el.just.value = '';
        Array.prototype.forEach.call(el.reasons.querySelectorAll('input'), function (i) { i.checked = false; });
        el.save.disabled = true;
    }

    el.approve.addEventListener('click', function () {
        decision = 'approve';
        el.approve.classList.add('sel');
        el.reject.classList.remove('sel');
        el.reasons.hidden = true;
        el.justWrap.hidden = true;
        el.save.disabled = false;
    });

    el.reject.addEventListener('click', function () {
        decision = 'reject';
        el.reject.classList.add('sel');
        el.approve.classList.remove('sel');
        el.reasons.hidden = false;
        el.justWrap.hidden = false;
        el.save.disabled = true;
    });

    function updateRejectState() {
        if (decision !== 'reject') return;
        var any = !!el.reasons.querySelector('input:checked');
        el.save.disabled = !(any && el.just.value.trim() !== '');
    }
    el.reasons.addEventListener('change', updateRejectState);
    el.just.addEventListener('input', updateRejectState);

    /**
     * SALVAR RESPOSTA:
     *  - APROVAR: valida que o revisor preencheu os 13 critérios no formulário
     *    nativo e submete ESSE formulário (salvamento nativo). Nunca marca
     *    critérios nem cria evidências. Não altera publication_mode.
     *  - NÃO APROVAR: submete ao handler nativo (admin_init) com nonce nativo.
     */
    el.save.addEventListener('click', function () {
        if (!selectedId) { showMsg('Selecione um artigo.', false); return; }
        if (!decision) { showMsg('Escolha uma decisão.', false); return; }

        if (decision === 'approve') {
            var form = document.getElementById(cfg.formId || 'cxgv1nat-native-form');
            if (!form) {
                showMsg('Formulário nativo do Gate não encontrado.', false);
                return;
            }
            // Não inventar evidências: exige que o humano tenha preenchido.
            var checks = form.querySelectorAll('input[name^="checked["]');
            var missing = 0, noEvidence = 0;
            Array.prototype.forEach.call(checks, function (c) {
                var name = c.getAttribute('name');
                var key = name.slice(name.indexOf('[') + 1, name.lastIndexOf(']'));

                if (!c.checked) { missing++; return; }
                var ev = form.querySelector('textarea[name="evidence[' + key + ']"]');
                if (!ev || ev.value.trim() === '') { noEvidence++; }
            });
            if (missing > 0 || noEvidence > 0 || checks.length === 0) {
                showMsg('Preencha os ' + checks.length + ' critérios humanos (faltam ' + missing +
                    ' e ' + noEvidence + ' sem evidência) no formulário nativo abaixo. O layout não marca nem inventa evidências.', false);
                return;
            }
            // Submete o formulário NATIVO — destino (publication_mode) preservado.
            showMsg('Aprovação pronta: confirming pelo mecanismo nativo do Gate…', true);
            if (typeof form.requestSubmit === 'function') { form.requestSubmit(); }
            else { form.submit(); }
            return;
        }

        // Reprovação: handler nativo, nonce nativo, histórico nativo.
        var checked = el.reasons.querySelectorAll('input:checked');
        if (!checked.length || !el.just.value.trim()) {
            showMsg('Selecione ao menos um motivo e escreva a justificativa.', false);
            return;
        }
        var data = new FormData();
        data.append('cxgv1nat_reject', '1');
        data.append('post_id', String(selectedId));
        data.append('snapshot_sha256', snapshot || '');
        var nonceInput = document.getElementById('cxgv1nat-native-form')
            ? document.getElementById('cxgv1nat-native-form').querySelector('input[name="_wpnonce"]')
            : null;
        data.append('_wpnonce', nonceInput ? nonceInput.value : '');
        Array.prototype.forEach.call(checked, function (i) { data.append('cxgv1nat_reason[]', i.value); });
        data.append('cxgv1nat_justification', el.just.value.trim());

        fetch(window.location.href, { method: 'POST', body: data, credentials: 'same-origin' })
        .then(function (r) { if (r.ok) { window.location.reload(); } else { showMsg('Falha ao registrar reprovação.', false); } })
        .catch(function () { showMsg('Falha de rede ao registrar reprovação.', false); });
    });

    Array.prototype.forEach.call(el.tabs, function (tab) {
        tab.addEventListener('click', function () {
            Array.prototype.forEach.call(el.tabs, function (t) { t.classList.remove('active'); });
            tab.classList.add('active');
            Array.prototype.forEach.call(document.querySelectorAll('.cxgv1nat-tabcontent'), function (c) { c.classList.remove('active'); });
            var target = document.getElementById('cxgv1nat-tab-' + tab.getAttribute('data-tab'));
            if (target) target.classList.add('active');
        });
    });

    function esc(s) {
        if (s === null || s === undefined) return '';
        var d = document.createElement('div'); d.textContent = String(s); return d.innerHTML;
    }
})();

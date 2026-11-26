/**
 * Gate V1 — layout nativo: preview dinâmico e decisão via formulário nativo.
 * NÃO cria endpoints novos: usa GET conexo/v1/editorial/snapshot/{id} (nativo)
 * e submete o formulário nativo existente no Gate.
 */
(function () {
    'use strict';
    var cfg = window.cxgv1nat_cfg || {};
    var root = document.getElementById('cxgv1nat-root');
    if (!root) return;

    var postId = parseInt(root.getAttribute('data-post-id'), 10);
    var snapshot = root.getAttribute('data-snapshot');
    var selected = null;
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

    function headers() {
        return { 'X-WP-Nonce': cfg.nonce || '' };
    }

    // Carrega lista de rascunhos elegíveis — somente leitura via endpoint nativo.
    function loadList() {
        fetch('?page=conexo-owner-review&cxgv1nat=list', { credentials: 'same-origin' })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.error) { showMsg(data.error, false); return; }
                var items = data.items || [];
                document.getElementById('cxgv1nat-total').textContent = data.total || 0;
                document.getElementById('cxgv1nat-ready').textContent = items.filter(function (i) { return i.status === 'ready'; }).length;
                document.getElementById('cxgv1nat-blocked').textContent = items.filter(function (i) { return i.status === 'blocked'; }).length;
                el.list.innerHTML = '';
                items.forEach(function (it) {
                    var div = document.createElement('div');
                    div.className = 'cxgv1nat-item';
                    div.setAttribute('data-id', it.id);
                    var thumb = it.thumbnail_url
                        ? '<img class="cxgv1nat-thumb" src="' + esc(it.thumbnail_url) + '" alt="' + esc(it.thumbnail_alt || '') + '">'
                        : '<div class="cxgv1nat-thumb-ph">Sem imagem</div>';
                    div.innerHTML = thumb + '<div><strong>' + esc(it.title) + '</strong>' +
                        '<div class="cxgv1nat-meta"><span>' + esc(fmtDate(it.date)) + '</span>' +
                        '<span class="cxgv1nat-pill ' + (it.status === 'blocked' ? 'blocked' : '') + '">' + esc(it.status) + '</span>' +
                        (it.categories || []).map(function (c) { return '<span>' + esc(c) + '</span>'; }).join('') +
                        '</div></div>';
                    div.addEventListener('click', function () { selectArticle(it); });
                    el.list.appendChild(div);
                });
            })
            .catch(function () { showMsg('Falha ao carregar fila.', false); });
    }

    // Preview dinâmico via endpoint nativo de snapshot (leitura autenticada).
    function selectArticle(item) {
        selected = item;
        Array.prototype.forEach.call(el.list.children, function (c) { c.classList.remove('sel'); });
        var target = el.list.querySelector('[data-id="' + item.id + '"]');
        if (target) target.classList.add('sel');

        fetch(cfg.apiBase + '/snapshot/' + item.id, { credentials: 'same-origin', headers: headers() })
            .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
            .then(function (data) {
                var snap = data.snapshot || {};
                snapshot = data.snapshot_sha256 || item.snapshot_sha256 || snapshot;
                root.setAttribute('data-snapshot', snapshot);
                el.detail.innerHTML = '<h4>' + esc(snap.post_title || item.title) + '</h4>' +
                    '<p class="cxgv1nat-sub2">' + esc(fmtDate(snap.post_modified || item.date)) + '</p>' +
                    '<div class="cxgv1nat-body">' + (snap.post_content || '') + '</div>';
                var pv = document.getElementById('cxgv1nat-tab-preview');
                if (pv) pv.innerHTML = el.detail.innerHTML;
                var det = document.getElementById('cxgv1nat-tab-details');
                if (det) det.innerHTML = '<p><strong>ID:</strong> ' + esc(item.id) + '</p>' +
                    '<p><strong>Status:</strong> ' + esc(snap.post_status || '') + '</p>' +
                    '<p><strong>Snapshot:</strong> <code>' + esc(snapshot) + '</code></p>';
                var vf = document.getElementById('cxgv1nat-tab-verification');
                if (vf) vf.innerHTML = (item.issues && item.issues.length)
                    ? '<ul>' + item.issues.map(function (i) { return '<li>' + esc(i) + '</li>'; }).join('') + '</ul>'
                    : '<p>Sem pendências técnicas detectadas.</p>';
                resetDecision();
            })
            .catch(function (e) { showMsg('Falha no preview: ' + e.message, false); });
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
        var anyReason = !!el.reasons.querySelector('input:checked');
        el.save.disabled = !(anyReason && el.just.value.trim() !== '');
    }
    el.reasons.addEventListener('change', updateRejectState);
    el.just.addEventListener('input', updateRejectState);

    // SALVAR RESPOSTA: preenche e submete o formulário NATIVO do Gate V1.
    el.save.addEventListener('click', function () {
        if (!selected) { showMsg('Selecione um artigo.', false); return; }
        if (!decision) { showMsg('Escolha uma decisão.', false); return; }

        var nativeForm = document.querySelector('form');
        if (!nativeForm) { showMsg('Formulário nativo do Gate não encontrado.', false); return; }

        if (decision === 'reject') {
            var checked = el.reasons.querySelectorAll('input:checked');
            if (!checked.length || !el.just.value.trim()) {
                showMsg('Motivo e justificativa são obrigatórios.', false);
                return;
            }
            // Reprovação: registra no mecanismo nativo via campo de evidência.
            var reasonText = Array.prototype.map.call(checked, function (i) { return i.value; }).join(', ');
            var firstCheck = nativeForm.querySelector('input[name="checked[versao]"]');
            var firstEv = nativeForm.querySelector('textarea[name="evidence[versao]"]');
            if (firstCheck) firstCheck.checked = false; // não aprova
            if (firstEv) firstEv.value = 'REPROVADO: ' + reasonText + ' — ' + el.just.value.trim();
            showMsg('Reprovação registrada no formulário nativo. Confirme abaixo.', true);
            return;
        }

        // Aprovação: marca os 13 checks nativos e o aceite, mantém destino 'hold'.
        Array.prototype.forEach.call(nativeForm.querySelectorAll('input[name^="checked["]'), function (c) { c.checked = true; });
        var accept = nativeForm.querySelector('input[name="owner_accept"]');
        if (accept) accept.checked = true;
        Array.prototype.forEach.call(nativeForm.querySelectorAll('input[name="publication_mode"]'), function (r) {
            if (r.value === 'hold') r.checked = true;
        });
        showMsg('Aprovação preparada no formulário nativo (destino: manter em espera). Confirme abaixo.', true);
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
    function fmtDate(s) {
        if (!s) return '';
        var d = new Date(s.replace(' ', 'T'));
        return isNaN(d.getTime()) ? s : d.toLocaleString('pt-BR');
    }

    loadList();
})();

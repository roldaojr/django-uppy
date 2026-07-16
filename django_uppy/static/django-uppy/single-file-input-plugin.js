/**
 * SingleFileInput — Plugin de UI para Uppy que imita um <input type="file">
 * de arquivo único, com barra de progresso.
 *
 * Uso:
 *   const uppy = new Uppy({ restrictions: { maxNumberOfFiles: 1 } })
 *   uppy.use(SingleFileInput, { target: '#area', buttonText: 'Escolher arquivo' })
 *
 * Depende apenas do core do Uppy (Uppy, @uppy/core). Sem frameworks.
 */
(function (global) {
  'use strict';

  // Base mínima própria — evita depender de Uppy.BasePlugin, que não é
  // exposto de forma confiável no bundle standalone (CDN) da v4/v5.
  // Precisa expor os hooks que o core chama em cada plugin montado:
  // update(state), afterUpdate(), get/setPluginState, setOptions.
  class BasePlugin {
    constructor(uppy, opts) {
      this.uppy = uppy;
      this.opts = opts || {};
    }
    getPluginState() {
      const plugins = this.uppy.getState().plugins || {};
      return plugins[this.id] || {};
    }
    setPluginState(update) {
      if (!update) return;
      const plugins = this.uppy.getState().plugins || {};
      this.uppy.setState({
        plugins: Object.assign({}, plugins, {
          [this.id]: Object.assign({}, plugins[this.id], update),
        }),
      });
    }
    setOptions(newOpts) {
      this.opts = Object.assign({}, this.opts, newOpts);
      this.update(this.uppy.getState());
    }
    // chamado pelo core a cada state update — re-renderiza a UI
    update() {
      if (this.container) this.render();
    }
    afterUpdate() {}
    mount(target) {
      const el = typeof target === 'string' ? document.querySelector(target) : target;
      if (!el) throw new Error('SingleFileInput: target não encontrado: ' + target);
      this._root = el;
      el.appendChild(this.render());
    }
    unmount() {
      if (this._root && this.container && this.container.parentNode === this._root) {
        this._root.removeChild(this.container);
      }
    }
  }

  function formatSize(bytes) {
    if (!bytes && bytes !== 0) return '';
    const u = ['B', 'KB', 'MB', 'GB'];
    let i = 0;
    let n = bytes;
    while (n >= 1024 && i < u.length - 1) { n /= 1024; i++; }
    return `${n.toFixed(i ? 1 : 0)} ${u[i]}`;
  }

  class SingleFileInput extends BasePlugin {
    constructor(uppy, opts) {
      super(uppy, opts);
      this.id = this.opts.id || 'SingleFileInput';
      this.type = 'acquirer';
      this.title = 'Single File Input';

      const defaults = {
        buttonText: 'Escolher arquivo',
        placeholder: 'Nenhum arquivo escolhido',
        accept: null,        // ex: 'image/*,.pdf'
        autoProceed: false,  // se true, faz upload assim que seleciona
        showSize: false,     // nativo não mostra tamanho; true para exibir
        showRemove: false,   // nativo não tem botão remover; true para exibir
      };
      this.opts = Object.assign({}, defaults, opts);

      // bind
      this.render = this.render.bind(this);
      this.handlePick = this.handlePick.bind(this);
      this.handleRemove = this.handleRemove.bind(this);
      this.onFileChange = this.onFileChange.bind(this);
      this.onProgress = this.onProgress.bind(this);
      this.onComplete = this.onComplete.bind(this);
      this.onError = this.onError.bind(this);
    }

    // ---- ciclo de vida ----
    install() {
      const target = this.opts.target;
      this.mount(target);

      this.uppy.on('file-added', this.onFileChange);
      this.uppy.on('file-removed', this.onFileChange);
      this.uppy.on('upload-progress', this.onProgress);
      this.uppy.on('upload-success', this.onComplete);
      this.uppy.on('complete', this.render);
      this.uppy.on('upload-error', this.onError);
      this.uppy.on('restriction-failed', this.onError);
    }

    uninstall() {
      this.uppy.off('file-added', this.onFileChange);
      this.uppy.off('file-removed', this.onFileChange);
      this.uppy.off('upload-progress', this.onProgress);
      this.uppy.off('upload-success', this.onComplete);
      this.uppy.off('complete', this.render);
      this.uppy.off('upload-error', this.onError);
      this.uppy.off('restriction-failed', this.onError);
      this.unmount();
    }

    // ---- helpers de estado ----
    getFile() {
      const files = this.uppy.getFiles();
      return files.length ? files[0] : null;
    }

    // ---- handlers ----
    handlePick() {
      if (this.hiddenInput) this.hiddenInput.click();
    }

    onFileChange() {
      this.errorMsg = null;
      this.render();
      if (this.opts.autoProceed && this.getFile()) {
        this.uppy.upload();
      }
    }

    handleRemove() {
      const f = this.getFile();
      if (f) this.uppy.removeFile(f.id);
      if (this.hiddenInput) this.hiddenInput.value = '';
    }

    onProgress(file, progress) {
      if (!this.progressBar) return;
      if (!progress || !progress.bytesTotal) return;
      const pct = Math.round((progress.bytesUploaded / progress.bytesTotal) * 100);
      this.setProgress(pct);
    }

    onComplete() {
      this.setProgress(100);
      this.render();
    }

    onError(fileOrError, err) {
      const msg = (err && err.message) ||
        (fileOrError && fileOrError.message) ||
        'Erro no upload';
      this.errorMsg = msg;
      this.render();
    }

    setProgress(pct) {
      if (this.progressBar) {
        this.progressBar.style.width = pct + '%';
        this.progressWrap.setAttribute('aria-valuenow', String(pct));
      }
      if (this.progressLabel) this.progressLabel.textContent = pct + '%';
    }

    // ---- render (DOM puro) ----
    render() {
      if (!this.container) this.buildStatic();

      const file = this.getFile();
      const uploading = file && file.progress && file.progress.uploadStarted && !file.progress.uploadComplete;
      const done = file && file.progress && file.progress.uploadComplete;

      // nome / placeholder
      if (file) {
        this.fileName.textContent = file.name;
        this.fileSize.textContent = this.opts.showSize ? formatSize(file.size) : '';
        this.fileName.classList.remove('sfi-empty');
      } else {
        this.fileName.textContent = this.opts.placeholder;
        this.fileSize.textContent = '';
        this.fileName.classList.add('sfi-empty');
      }

      // botão remover (oculto por padrão — nativo não tem)
      this.removeBtn.style.display = (file && this.opts.showRemove) ? '' : 'none';

      // barra de progresso: visível se há arquivo com upload em andamento/concluído
      const showBar = !!(file && file.progress && (file.progress.uploadStarted || done));
      this.progressWrap.style.display = showBar ? '' : 'none';
      this.progressBar.classList.toggle('sfi-done', !!done);

      if (done) this.setProgress(100);

      // erro
      if (this.errorMsg) {
        this.errorEl.textContent = this.errorMsg;
        this.errorEl.style.display = '';
      } else {
        this.errorEl.style.display = 'none';
      }

      return this.container;
    }

    buildStatic() {
      const doc = document;
      const wrap = doc.createElement('div');
      wrap.className = 'sfi';

      // input file oculto
      const input = doc.createElement('input');
      input.type = 'file';
      input.className = 'sfi-hidden-input';
      input.style.display = 'none';
      if (this.opts.accept) input.accept = this.opts.accept;
      input.addEventListener('change', (e) => {
        const files = e.target.files;
        if (!files || !files.length) return;
        // limpa arquivo anterior (single file)
        const existing = this.getFile();
        if (existing) this.uppy.removeFile(existing.id);
        const f = files[0];
        try {
          this.uppy.addFile({ name: f.name, type: f.type, data: f, source: this.id });
        } catch (err) {
          this.onError(null, err);
        }
      });
      this.hiddenInput = input;

      // linha principal: [botão] [nome+tamanho] [remover]
      const row = doc.createElement('div');
      row.className = 'sfi-row';

      const btn = doc.createElement('button');
      btn.type = 'button';
      btn.className = 'sfi-btn';
      btn.textContent = this.opts.buttonText;
      btn.addEventListener('click', this.handlePick);

      const info = doc.createElement('div');
      info.className = 'sfi-info';
      const nameEl = doc.createElement('span');
      nameEl.className = 'sfi-name sfi-empty';
      nameEl.textContent = this.opts.placeholder;
      const sizeEl = doc.createElement('span');
      sizeEl.className = 'sfi-size';
      info.appendChild(nameEl);
      info.appendChild(sizeEl);

      const removeBtn = doc.createElement('button');
      removeBtn.type = 'button';
      removeBtn.className = 'sfi-remove';
      removeBtn.setAttribute('aria-label', 'Remover arquivo');
      removeBtn.textContent = '×';
      removeBtn.style.display = 'none';
      removeBtn.addEventListener('click', this.handleRemove);

      row.appendChild(btn);
      row.appendChild(info);
      row.appendChild(removeBtn);

      // barra de progresso
      const progWrap = doc.createElement('div');
      progWrap.className = 'sfi-progress';
      progWrap.setAttribute('role', 'progressbar');
      progWrap.setAttribute('aria-valuemin', '0');
      progWrap.setAttribute('aria-valuemax', '100');
      progWrap.style.display = 'none';
      const bar = doc.createElement('div');
      bar.className = 'sfi-progress-bar';
      bar.style.width = '0%';
      const label = doc.createElement('span');
      label.className = 'sfi-progress-label';
      label.textContent = '0%';
      progWrap.appendChild(bar);
      progWrap.appendChild(label);

      // erro
      const errEl = doc.createElement('div');
      errEl.className = 'sfi-error';
      errEl.style.display = 'none';

      wrap.appendChild(input);
      wrap.appendChild(row);
      wrap.appendChild(progWrap);
      wrap.appendChild(errEl);

      this.container = wrap;
      this.fileName = nameEl;
      this.fileSize = sizeEl;
      this.removeBtn = removeBtn;
      this.progressWrap = progWrap;
      this.progressBar = bar;
      this.progressLabel = label;
      this.errorEl = errEl;

      this.injectStyles();
    }

    injectStyles() {
      if (document.getElementById('sfi-styles')) return;
      const style = document.createElement('style');
      style.id = 'sfi-styles';
      style.textContent = `
.sfi { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, Arial, sans-serif; max-width: 480px; }
.sfi-row { display: inline-flex; align-items: center; gap: 8px; }
.sfi-btn { flex: 0 0 auto; cursor: default;
  font-size: 13.333px; font-family: inherit; color: #000;
  background: #f0f0f0; border: 1px solid #767676; border-radius: 3px;
  padding: 1px 8px; line-height: normal; }
.sfi-btn:hover { background: #e5e5e5; border-color: #4f4f4f; }
.sfi-btn:active { background: #d5d5d5; }
.sfi-info { flex: 1 1 auto; min-width: 0; display: inline-flex; align-items: baseline; gap: 6px; }
.sfi-name { font-size: 13.333px; color: #000;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sfi-name.sfi-empty { color: #000; }
.sfi-size { font-size: 11px; color: #6a6a6a; flex: 0 0 auto; }
.sfi-remove { flex: 0 0 auto; border: none; background: transparent; color: #999;
  font-size: 16px; line-height: 1; cursor: pointer; padding: 0 4px; }
.sfi-remove:hover { color: #c00; }
.sfi-progress { position: relative; height: 6px; background: #e5e5e5;
  border-radius: 3px; margin-top: 6px; max-width: 480px; overflow: hidden; }
.sfi-progress-bar { height: 100%; width: 0%; background: #2186eb;
  transition: width .2s ease; }
.sfi-progress-bar.sfi-done { background: #31b237; }
.sfi-progress-label { position: absolute; right: 4px; top: -16px; font-size: 11px; color: #6a6a6a; }
.sfi-error { color: #c00; font-size: 12px; margin-top: 4px; }
`;
      document.head.appendChild(style);
    }
  }

  // export (global + CommonJS)
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = SingleFileInput;
  }
  if (typeof window !== 'undefined') {
    window.SingleFileInput = SingleFileInput;
  }
})(typeof window !== 'undefined' ? window : this);
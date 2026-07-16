
const plugins = {
  Dashboard: Uppy.Dashboard,
  Tus: Uppy.Tus,
  AwsS3: Uppy.AwsS3,
  SingleFileInput: window.SingleFileInput
};

function loadWidgets() {
  const uppyWidgets = document.querySelectorAll(".uppy-widget");
  for (let widget of uppyWidgets) {
    const pluginsJson = JSON.parse(widget.getAttribute("data-uppy-plugins"));
    const configJson = JSON.parse(widget.getAttribute("data-uppy-config"));
    const targetId = widget.getAttribute("data-target");
    const target = document.getElementById(targetId);
    const form = target.form;
    const isInitial = !!target.value;
    form.uploadsComplete = form.uploadsComplete || {};
    form.uploadsComplete[targetId] = isInitial;
    const uppy = new Uppy.Uppy(configJson || {});
    uppy.use(Uppy.Form, {
      target: widget.closest("form"),
      triggerUploadOnSubmit: true,
      submitOnSuccess: false,
      addResultToForm: false,
    });
    console.log(pluginsJson);
    for (const [name, config] of Object.entries(pluginsJson || {})) {
      console.debug("Use plugin", name, config);
      uppy.use(plugins[name], config);
    }
    uppy.on("upload-success", (file, response) => {
      const uploadUrl = response.uploadURL; 
      const uploadId = uploadUrl.substring(uploadUrl.lastIndexOf('/') + 1);
      target.value = `${uploadId}//${file.name}`;
      form.uploadsComplete[targetId] = true;
    });
    uppy.on("complete", (result) => {
      // Check if all uploads are complete
      if (Object.values(form.uploadsComplete).every(status => status)) {
        console.warn("All uploads complete!");
        const formData = new FormData(form);
        const data = Object.fromEntries(formData);
        console.log(data);
        form.submit();
      }
    });
    if(isInitial) {
      // exsintg file
      uppy.addFile({
        source: 'initial',
        name: target.value,
        type: 'file',
        data: new Blob(),
        uploadURL: target.dataset.url,
        progress: {
          percentage: 100,
          uploadComplete: true,
          uploadStarted: Date.now(),
        },
      });
      uppy.on("file-removed", (e) => {
        // Mark file as removed on form
        console.log(e)
      })
    }
  }
}

document.addEventListener('DOMContentLoaded', loadWidgets);

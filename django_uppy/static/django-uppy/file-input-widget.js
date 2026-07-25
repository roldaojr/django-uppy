const plugins = {
  Dashboard: Uppy.Dashboard,
  Tus: Uppy.Tus,
  AwsS3: Uppy.AwsS3,
  SingleFileInput: window.SingleFileInput
};

function initUppyFileInput(widget, prefix = undefined) {
  if(prefix) {
    // update dataset values
    Object.keys(widget.dataset).forEach(key => {
      widget.dataset[key] = widget.dataset[key].replace("__prefix__", prefix);
    });
  }
  const targetId = widget.dataset.target;
  const target = document.getElementById(targetId);
  if(target.name.includes("__prefix__")) return; // skip formset template
  if(target.uppy) return; // skip already loaded
  const form = target.form;
  // handle form set add
  if(!form.dataset.hasFormsetListener) {
    form.addEventListener("formset:added", function(e) {
      const prefix = e.target.id.split("-").pop();
      const newWidget = e.target.querySelector(".uppy-widget");
      initUppyFileInput(newWidget, prefix);
    });
    form.dataset.hasFormsetListener = "true";
  }
  //
  const pluginsJson = JSON.parse(widget.dataset.uppyPlugins);
  const configJson = JSON.parse(widget.dataset.uppyConfig);
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
  uppy.on("complete", () => {
    // Check if all uploads are complete
    if (Object.values(form.uploadsComplete).every(status => status)) {
      console.warn("All uploads complete!");
      const formData = new FormData(form);
      const data = Object.fromEntries(formData);
      console.log(data);
      form.submit();
    }
  });
  target.uppy = uppy;
}

document.addEventListener('DOMContentLoaded', () => {
  const widgets = document.querySelectorAll(".uppy-widget");
    for (let widget of widgets) {
      initUppyFileInput(widget);
    }
  }
);

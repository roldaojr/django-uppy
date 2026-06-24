import {
  Uppy,
  Form,
  Dashboard,
  Tus,
  AwsS3,
} from "https://releases.transloadit.com/uppy/v5.2.1/uppy.min.mjs";

const plugins = { Dashboard, Tus, AwsS3 };

const uppyWidgets = document.querySelectorAll(".uppy-widget");
for (let widget of uppyWidgets) {
  const pluginsJson = JSON.parse(widget.getAttribute("data-uppy-plugins"));
  const configJson = JSON.parse(widget.getAttribute("data-uppy-config"));
  const targetId = widget.getAttribute("data-target");
  const target = document.getElementById(targetId);
  const form = target.form;
  form.uploadsComplete = form.uploadsComplete || {};
  form.uploadsComplete[targetId] = false;
  const uppy = new Uppy(configJson || {});
  uppy.use(Form, {
    target: widget.closest("form"),
    triggerUploadOnSubmit: true,
    submitOnSuccess: false,
    addResultToForm: false,
  });
  for (const [name, config] of Object.entries(pluginsJson || {})) {
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
}

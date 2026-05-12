import {
  Uppy,
  Form,
  Dashboard,
  Tus,
  AwsS3,
} from "https://releases.transloadit.com/uppy/v5.2.1/uppy.min.mjs";

const plugins = { Dashboard, Tus, AwsS3 };

const uppyWidget = document.querySelectorAll(".uppy-widget");
for (let widget of uppyWidget) {
  console.log("widget", widget);
  const pluginsJsom = JSON.parse(widget.getAttribute("data-uppy-plugins"));
  const configJson = JSON.parse(widget.getAttribute("data-uppy-config"));
  const targetId = widget.getAttribute("data-target");
  const uppy = new Uppy(configJson || {});
  uppy.use(Form, {
    target: widget.closest("form"),
    triggerUploadOnSubmit: true,
    submitOnSuccess: false,
    addResultToForm: false,
  });
  for (const [name, config] of Object.entries(pluginsJsom || {})) {
    uppy.use(plugins[name], config);
  }
  uppy.on("complete", (result) => {
    const target = document.getElementById(targetId);
    console.log("Upload complete:", result);
    console.log("target", target, targetId, widget);
    if (result.successful.length > 0 && target) {
      const fileName = result.successful[0].name;
      console.log("Upload successful:", fileName);
      target.value = `${result.upload_id}//${fileName}`;
    }
  });
}

(function () {
  const dropzone = document.getElementById("compress-dropzone");
  const input = document.getElementById("compress-file");
  const fileList = document.getElementById("compress-file-list");
  const submitBtn = document.getElementById("compress-submit");
  const status = document.getElementById("compress-status");
  const result = document.getElementById("compress-result");
  const stat = document.getElementById("compress-stat");
  const downloadLink = document.getElementById("compress-download");
  const form = document.getElementById("compress-form");

  let chosenFile = null;

  setupDropzone(dropzone, input, (files) => {
    chosenFile = files[0] || null;
    renderFileList(fileList, chosenFile ? [chosenFile] : []);
    submitBtn.disabled = !chosenFile;
    status.textContent = "";
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!chosenFile) return;

    submitBtn.disabled = true;
    status.textContent = "Compressing...";
    status.className = "status";
    result.classList.remove("show");

    const fd = new FormData();
    fd.append("file", chosenFile);
    const maxKb = document.getElementById("target-max-kb").value;
    const minKb = document.getElementById("target-min-kb").value;
    if (maxKb) fd.append("target_max_kb", maxKb);
    if (minKb) fd.append("target_min_kb", minKb);

    await submitForm("/api/compress", fd, {
      onSuccess: (url, headers) => {
        status.textContent = "Done.";
        status.className = "status success";
        const orig = headers.get("X-Original-Size-KB");
        const compressed = headers.get("X-Compressed-Size-KB");
        stat.textContent = `${orig} KB \u2192 ${compressed} KB`;
        downloadLink.href = url;
        result.classList.add("show");
        submitBtn.disabled = false;
      },
      onError: (msg) => {
        status.textContent = msg;
        status.className = "status error";
        submitBtn.disabled = false;
      },
    });
  });
})();

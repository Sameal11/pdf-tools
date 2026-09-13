(function () {
  const dropzone = document.getElementById("word-dropzone");
  const input = document.getElementById("word-file");
  const fileList = document.getElementById("word-file-list");
  const submitBtn = document.getElementById("word-submit");
  const status = document.getElementById("word-status");
  const result = document.getElementById("word-result");
  const stat = document.getElementById("word-stat");
  const downloadLink = document.getElementById("word-download");
  const form = document.getElementById("word-form");

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
    status.textContent = "Converting... this can take a moment for scanned pages.";
    status.className = "status";
    result.classList.remove("show");

    const fd = new FormData();
    fd.append("file", chosenFile);
    fd.append("force_ocr", document.getElementById("force-ocr").checked ? "true" : "false");

    await submitForm("/api/pdf-to-word", fd, {
      onSuccess: (url, headers) => {
        status.textContent = "Done.";
        status.className = "status success";
        const usedOcr = headers.get("X-Used-OCR") === "true";
        stat.textContent = usedOcr ? "Converted using OCR (scanned pages detected)." : "Converted from text layer.";
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

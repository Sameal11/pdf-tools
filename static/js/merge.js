(function () {
  const dropzone = document.getElementById("merge-dropzone");
  const input = document.getElementById("merge-files");
  const fileList = document.getElementById("merge-file-list");
  const submitBtn = document.getElementById("merge-submit");
  const status = document.getElementById("merge-status");
  const result = document.getElementById("merge-result");
  const stat = document.getElementById("merge-stat");
  const downloadLink = document.getElementById("merge-download");
  const form = document.getElementById("merge-form");

  let chosenFiles = [];

  setupDropzone(dropzone, input, (files) => {
    chosenFiles = Array.from(files);
    renderFileList(fileList, chosenFiles);
    submitBtn.disabled = chosenFiles.length < 2;
    status.textContent = chosenFiles.length === 1 ? "Add at least one more PDF to merge." : "";
    status.className = "status";
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (chosenFiles.length < 2) return;

    submitBtn.disabled = true;
    status.textContent = "Merging...";
    status.className = "status";
    result.classList.remove("show");

    const fd = new FormData();
    chosenFiles.forEach((f) => fd.append("files", f));
    fd.append("add_page_numbers", document.getElementById("add-page-numbers").checked ? "true" : "false");
    fd.append("watermark_text", document.getElementById("watermark-text").value);

    await submitForm("/api/merge", fd, {
      onSuccess: (url) => {
        status.textContent = "Done.";
        status.className = "status success";
        stat.textContent = `${chosenFiles.length} files merged.`;
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

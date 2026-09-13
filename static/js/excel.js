(function () {
  const dropzone = document.getElementById("excel-dropzone");
  const input = document.getElementById("excel-file");
  const fileList = document.getElementById("excel-file-list");
  const submitBtn = document.getElementById("excel-submit");
  const status = document.getElementById("excel-status");
  const result = document.getElementById("excel-result");
  const stat = document.getElementById("excel-stat");
  const downloadLink = document.getElementById("excel-download");
  const form = document.getElementById("excel-form");

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
    status.textContent = "Extracting tables...";
    status.className = "status";
    result.classList.remove("show");

    const fd = new FormData();
    fd.append("file", chosenFile);

    await submitForm("/api/pdf-to-excel", fd, {
      onSuccess: (url) => {
        status.textContent = "Done.";
        status.className = "status success";
        stat.textContent = "Spreadsheet ready.";
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

// Shared helpers used by every tool page.

function formatSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(2) + " MB";
}

function setupDropzone(dropzoneEl, inputEl, onFilesChosen) {
  dropzoneEl.addEventListener("click", () => inputEl.click());
  dropzoneEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") inputEl.click();
  });

  ["dragenter", "dragover"].forEach((evt) =>
    dropzoneEl.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzoneEl.classList.add("drag-over");
    })
  );
  ["dragleave", "drop"].forEach((evt) =>
    dropzoneEl.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzoneEl.classList.remove("drag-over");
    })
  );
  dropzoneEl.addEventListener("drop", (e) => {
    const files = e.dataTransfer.files;
    inputEl.files = files;
    onFilesChosen(files);
  });
  inputEl.addEventListener("change", () => onFilesChosen(inputEl.files));
}

function renderFileList(listEl, files) {
  listEl.innerHTML = "";
  Array.from(files).forEach((f) => {
    const li = document.createElement("li");
    li.innerHTML = `<span>${f.name}</span><span class="size">${formatSize(f.size)}</span>`;
    listEl.appendChild(li);
  });
}

async function submitForm(url, formData, { onSuccess, onError, filename }) {
  try {
    const resp = await fetch(url, { method: "POST", body: formData });
    if (!resp.ok) {
      const data = await resp.json().catch(() => ({}));
      onError(data.error || `Request failed (${resp.status})`);
      return;
    }
    const blob = await resp.blob();
    const downloadUrl = URL.createObjectURL(blob);
    onSuccess(downloadUrl, resp.headers);
  } catch (err) {
    onError("Something went wrong. Check your connection and try again.");
  }
}

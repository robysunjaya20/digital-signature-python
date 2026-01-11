async function sign() {
  const file = document.getElementById("file").files[0];
  const form = new FormData();
  form.append("file", file);

  const res = await fetch("http://localhost:8000/sign", {
    method: "POST",
    body: form
  });

  alert(await res.text());
}

async function verify() {
  const doc = document.getElementById("doc").files[0];
  const sig = document.getElementById("sig").files[0];

  const form = new FormData();
  form.append("file", doc);
  form.append("signature", sig);

  const res = await fetch("http://localhost:8000/verify", {
    method: "POST",
    body: form
  });

  alert(await res.text());
}

$("#delete-film-modal").on("show.bs.modal", function (event) {
  let url = event.relatedTarget.dataset.url;
  let form = this.querySelector("form");
  form.action = url;
  let filmName = event.relatedTarget.closest("tr").querySelector(".film-name")
    .textContent;
  this.querySelector("#film-name").textContent = filmName;
});

$("#create-collection-modal").on("show.bs.modal", function (event) {
  let url = event.relatedTarget.dataset.url;
  let form = this.querySelector("form");
  form.action = url;
});

$("#to-collection-modal").on("show.bs.modal", function (event) {
  let url = event.relatedTarget.dataset.url;
  let form = this.querySelector("form");
  form.action = url;
});



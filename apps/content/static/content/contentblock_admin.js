/*
 * Fills a ContentBlock's "data" field with a valid, all-three-languages
 * skeleton the moment its block_type is picked — the shapes here mirror
 * apps/content/block_schemas.py exactly, so update both together. This is
 * the single biggest source of admin mistakes: forgetting a language or
 * misspelling a key, which the backend now rejects on save anyway, but a
 * correct starting point is better than a rejection round-trip.
 */
(function () {
  var SKELETONS = {
    heading: { uz: { text: "" }, ru: { text: "" }, en: { text: "" } },
    paragraph: { uz: { text: "" }, ru: { text: "" }, en: { text: "" } },
    list: { uz: { items: [""] }, ru: { items: [""] }, en: { items: [""] } },
    staff_card: {
      uz: { full_name: "", title: "" },
      ru: { full_name: "", title: "" },
      en: { full_name: "", title: "" },
    },
    image: {
      uz: { image_id: null, alt: "" },
      ru: { image_id: null, alt: "" },
      en: { image_id: null, alt: "" },
    },
    video: {
      uz: { video_id: null, caption: "" },
      ru: { video_id: null, caption: "" },
      en: { video_id: null, caption: "" },
    },
    document: {
      uz: { document_id: null, caption: "" },
      ru: { document_id: null, caption: "" },
      en: { document_id: null, caption: "" },
    },
  };

  document.addEventListener("change", function (event) {
    var select = event.target;
    if (!select.matches("select") || !/block_type$/.test(select.name)) return;

    var dataFieldName = select.name.slice(0, -"block_type".length) + "data";
    var dataField = document.querySelector('[name="' + dataFieldName + '"]');
    if (!dataField) return;
    // Django's JSONField widget renders an empty value as the literal text
    // "null", not blank — treat both as "nothing typed yet" so autofill can
    // still kick in, but never as the string once real content is typed.
    var current = dataField.value.trim();
    if (current !== "" && current !== "null") return;

    var skeleton = SKELETONS[select.value];
    if (skeleton) dataField.value = JSON.stringify(skeleton, null, 2);
  });
})();

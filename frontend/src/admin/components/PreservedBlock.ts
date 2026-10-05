import { Node, mergeAttributes } from "@tiptap/react";

/**
 * A content block the rich-text editor cannot express as HTML -- a table, an
 * embedded PDF/document, a photo gallery, a staff card, legacy raw HTML -- sent
 * by the API as `<div data-preserved-block="<id>" ...>label</div>` (see
 * apps/content/admin_content.py).
 *
 * Without this node TipTap would silently strip the unknown <div> on load, and
 * the server would then read its absence as "the editor deleted this block":
 * merely opening a page and pressing Save used to wipe every table and PDF on
 * it. As an atomic node it survives load -> edit -> save untouched, can be
 * dragged to another position (the server re-orders the block to match), and
 * is deleted only when the editor selects it and presses Delete/Backspace.
 */
export const PreservedBlock = Node.create({
  name: "preservedBlock",
  group: "block",
  atom: true,
  selectable: true,
  draggable: true,

  addAttributes() {
    return {
      blockId: {
        default: null,
        parseHTML: (element) => element.getAttribute("data-preserved-block"),
        renderHTML: (attributes) => ({ "data-preserved-block": attributes.blockId }),
      },
      blockType: {
        default: "",
        parseHTML: (element) => element.getAttribute("data-block-type") ?? "",
        renderHTML: (attributes) => ({ "data-block-type": attributes.blockType }),
      },
      label: {
        default: "",
        parseHTML: (element) => element.textContent ?? "",
        renderHTML: () => ({}),
      },
      // A file just uploaded through the toolbar ("Fayl qo'shish"): no block exists for it yet, so it is sent
      // as <div data-new-document="<media path>" data-title="..."> and the server creates the document card
      // on save (see _materialize_new_documents in apps/content/admin_content.py).
      newDocument: {
        default: null,
        parseHTML: (element) => element.getAttribute("data-new-document"),
        renderHTML: (attributes) => (attributes.newDocument ? { "data-new-document": attributes.newDocument } : {}),
      },
      docTitle: {
        default: "",
        parseHTML: (element) => element.getAttribute("data-title") ?? "",
        renderHTML: (attributes) => (attributes.docTitle ? { "data-title": attributes.docTitle } : {}),
      },
    };
  },

  parseHTML() {
    return [{ tag: "div[data-preserved-block]" }, { tag: "div[data-new-document]" }];
  },

  renderHTML({ node, HTMLAttributes }) {
    return ["div", mergeAttributes(HTMLAttributes, { class: "preserved-block" }), node.attrs.label];
  },
});

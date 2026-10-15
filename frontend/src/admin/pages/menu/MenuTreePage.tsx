import { useEffect, useRef, useState } from "react";
import { getMenuTree, createMenuNode, updateMenuNode, deleteMenuNode, moveMenuNode } from "@/api/adminMenu";
import type { AdminMenuNode } from "@/admin/menuTypes";
import type { MenuNodeInput, MovePosition } from "@/api/adminMenu";
import MenuTreeNode from "@/admin/components/MenuTreeNode";
import MenuNodeEditor from "@/admin/components/MenuNodeEditor";
import PageHeader from "@/admin/components/PageHeader";
import { useConfirm } from "@/admin/components/ConfirmDialog";
import { useToast } from "@/admin/components/Toast";

function findNode(nodes: AdminMenuNode[], id: number): AdminMenuNode | null {
  for (const n of nodes) {
    if (n.id === id) return n;
    const found = findNode(n.children, id);
    if (found) return found;
  }
  return null;
}

function findParentId(nodes: AdminMenuNode[], id: number, parent: number | null = null): number | null {
  for (const n of nodes) {
    if (n.id === id) return parent;
    const found = findParentId(n.children, id, n.id);
    if (found !== null) return found;
  }
  return null;
}

export default function MenuTreePage() {
  const [tree, setTree] = useState<AdminMenuNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [draggingId, setDraggingId] = useState<number | null>(null);
  // The drop decision reads this ref (updated synchronously in onDragStart),
  // not the `draggingId` state above — state is only for the dimming visual.
  // A native drag always has a real dragover in between (the user physically
  // moves the mouse), which is enough for React to flush state in practice,
  // but the ref removes any dependency on that timing assumption entirely.
  const draggingIdRef = useRef<number | null>(null);
  const [error, setError] = useState("");
  const toast = useToast();
  const confirm = useConfirm();

  async function load() {
    setLoading(true);
    try {
      const data = await getMenuTree();
      setTree(data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const selectedNode = selectedId != null ? findNode(tree, selectedId) : null;

  async function onAddRoot() {
    const created = await createMenuNode({
      parentId: null,
      title_uz: "Yangi bo'lim",
      title_ru: "Новый раздел",
      title_en: "New section",
      url_type: "other",
      url_value: "#",
      status: 1,
      active: 1,
      disabled: 0,
    });
    await load();
    setSelectedId(created.id);
  }

  async function onAddChild(parent: AdminMenuNode) {
    const created = await createMenuNode({
      parentId: parent.id,
      title_uz: "Yangi element",
      title_ru: "Новый элемент",
      title_en: "New item",
      url_type: "other",
      url_value: "#",
      status: 1,
      active: 1,
      disabled: 0,
    });
    await load();
    setSelectedId(created.id);
  }

  async function onDelete(node: AdminMenuNode) {
    const childWarning = node.children.length > 0 ? ` (va uning ${node.children.length} ta ichki elementi)` : "";
    const ok = await confirm({
      title: `«${node.titleUz}» menyudan o'chirilsinmi?`,
      message: `${childWarning ? `Uning ichidagi ${node.children.length} ta element ham yo'qoladi. ` : ""}Sahifaning o'zi o'chmaydi, faqat menyudan olib tashlanadi.`,
      confirmLabel: "Ha, o'chirish",
      danger: true,
    });
    if (!ok) return;
    await deleteMenuNode(node.id);
    if (selectedId === node.id) setSelectedId(null);
    await load();
  }

  async function onSave(input: MenuNodeInput) {
    if (!selectedNode) return;
    await updateMenuNode(selectedNode.id, input);
    await load();
    toast.success("Menyu saqlandi.");
  }

  async function onDrop(info: { nodeId: number; position: MovePosition }) {
    const sourceId = draggingIdRef.current;
    if (sourceId == null) return;
    setError("");
    try {
      await moveMenuNode(sourceId, info.nodeId, info.position);
      await load();
    } catch {
      setError("Ko'chirishda xatolik yuz berdi (masalan, elementni o'zining ichiga ko'chirib bo'lmaydi).");
    }
    draggingIdRef.current = null;
    setDraggingId(null);
  }

  return (
    <div className="mx-auto max-w-6xl">
      <PageHeader
        title="Menyu daraxti"
        subtitle="Saytning yuqori menyusi. Elementlarni sudrab tartibini o'zgartiring: yuqori/pastki chetiga tashlansa — yonma-yon, o'rtasiga tashlansa — ichiga joylashadi."
        actions={
          <button onClick={onAddRoot} className="flex h-10 cursor-pointer items-center gap-2 rounded-lg bg-primary-500 px-4 text-sm font-semibold text-background-50 hover:bg-primary-600">
            <i className="ri-add-line" aria-hidden="true" /> Yangi bo'lim
          </button>
        }
      />

      {error && <div className="mb-4 p-3 rounded-md bg-red-50 border border-red-200 text-sm text-red-800">{error}</div>}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 rounded-xl border border-background-200 bg-background-50 p-3">
          {loading ? (
            <div className="py-16 flex justify-center">
              <i className="ri-loader-4-line w-8 h-8 flex items-center justify-center animate-spin text-primary-500 text-3xl" />
            </div>
          ) : (
            tree.map((node) => (
              <MenuTreeNode
                key={node.id}
                node={node}
                depth={0}
                selectedId={selectedId}
                draggingId={draggingId}
                onSelect={(n) => setSelectedId(n.id)}
                onAddChild={onAddChild}
                onDelete={onDelete}
                onDragStart={(n) => {
                  draggingIdRef.current = n.id;
                  setDraggingId(n.id);
                }}
                onDragEnd={() => {
                  draggingIdRef.current = null;
                  setDraggingId(null);
                }}
                onDrop={onDrop}
              />
            ))
          )}
        </div>

        <div className="lg:sticky lg:top-20 lg:self-start">
          {selectedNode ? (
            <MenuNodeEditor node={selectedNode} parentId={findParentId(tree, selectedNode.id)} onSave={onSave} onClose={() => setSelectedId(null)} />
          ) : (
            <div className="rounded-xl border border-dashed border-background-300 bg-background-50 p-6 text-center text-sm text-foreground-500">
              Tahrirlash uchun chapdan biror elementni tanlang.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

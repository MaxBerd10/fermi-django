import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { listVideo } from "@/api/video";
import type { VideoItem } from "@/types/content";
import { Reveal } from "@/components/Animation";
import PageHeader from "@/components/shared/PageHeader";
import NewsSectionLayout from "@/components/shared/NewsSectionLayout";
import NewsPagination from "@/components/shared/NewsPagination";
import { LoadingState } from "@/components/shared/LoadingState";
import { usePageMeta } from "@/hooks/usePageMeta";

// The uploaded clips are served without HTTP range support, so even
// preload="metadata" pulls the entire file rather than just its header --
// with up to 9 cards per page all doing this at once on mount, the page felt
// like it was loading every video's full weight before anything was
// interactive. Only start loading a card once it's actually about to be
// visible (a lazily-created IntersectionObserver, one per grid), so a visit
// only ever pays for the clips it scrolls to.
function useLazyVisible<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el || visible) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin: "300px" },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [visible]);

  return { ref, visible };
}

// preload="metadata" alone isn't enough in every browser to paint a first-frame
// thumbnail — some just show a blank/black box until playback starts. Seeking a
// hair into the clip once metadata is ready forces the browser to decode and
// paint that frame, which is what actually produces a visible thumbnail.
function VideoCard({ src }: { src: string }) {
  const { ref: wrapRef, visible } = useLazyVisible<HTMLDivElement>();
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !visible) return;
    const onLoadedMetadata = () => {
      try {
        video.currentTime = 0.1;
      } catch {
        // ignore — some browsers throw if the media isn't seekable yet
      }
    };
    video.addEventListener("loadedmetadata", onLoadedMetadata);
    return () => video.removeEventListener("loadedmetadata", onLoadedMetadata);
  }, [visible]);

  return (
    <div ref={wrapRef} className="w-full h-full">
      {visible && <video ref={videoRef} src={src} controls preload="metadata" className="w-full h-full object-cover" />}
    </div>
  );
}

function YoutubeCard({ videoId }: { videoId: string }) {
  const { ref, visible } = useLazyVisible<HTMLDivElement>();
  return (
    <div ref={ref} className="w-full h-full">
      {visible && (
        <iframe src={`https://www.youtube.com/embed/${videoId}`} title={`Video ${videoId}`} allowFullScreen />
      )}
    </div>
  );
}

export default function VideoPage() {
  const { t } = useTranslation();
  usePageMeta(t("video.title"));
  const [searchParams] = useSearchParams();
  const page = Number(searchParams.get("page") || "1");
  const [items, setItems] = useState<VideoItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    listVideo(page)
      .then((res) => {
        setItems(res.data);
        setTotal(res.meta?.total ?? res.data.length);
      })
      .finally(() => setLoading(false));
  }, [page]);

  const pageSize = 9;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="text-foreground-950">
      <PageHeader title={t("video.title")} breadcrumb={t("news.title")} compact />

      <NewsSectionLayout intro={t("video.intro")}>
        {loading ? (
          <LoadingState />
        ) : (
          <>
            <Reveal>
              <div className="news-video-grid">
                {items.map((v) => (
                  <div key={v.id} className="news-video-card">
                    {v.url ? (
                      <YoutubeCard videoId={v.url} />
                    ) : v.video ? (
                      <VideoCard src={v.video} />
                    ) : null}
                  </div>
                ))}
              </div>
            </Reveal>

            <Reveal delay={200}>
              <NewsPagination page={page} totalPages={totalPages} />
            </Reveal>
          </>
        )}
      </NewsSectionLayout>
    </div>
  );
}

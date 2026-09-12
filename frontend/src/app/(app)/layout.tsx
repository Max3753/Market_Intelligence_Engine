import Sidebar from "@/components/Sidebar";
import PageTransition from "@/components/PageTransition";
import MotionProvider from "@/components/MotionProvider";

/**
 * 应用壳布局 —— 仪表盘/需求/机会/簇/控制台共用的 Sidebar + 主内容区。
 * 路由组 (app) 内的页面共享此布局；落地页（/）不经过这里。
 */
export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative z-10 flex h-screen overflow-hidden">
      <Sidebar />
      <main className="relative z-10 flex-1 overflow-y-auto p-4 md:p-8">
        <div className="mx-auto max-w-7xl">
          <MotionProvider>
            <PageTransition>{children}</PageTransition>
          </MotionProvider>
        </div>
      </main>
    </div>
  );
}
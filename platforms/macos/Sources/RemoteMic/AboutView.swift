import AppKit
import SwiftUI

enum AboutInformation {
    static let appName = "MiVibe Remote"
    static func versionText(infoDictionary: [String: Any]) -> String {
        let shortVersion = (infoDictionary["CFBundleShortVersionString"] as? String)?
            .trimmingCharacters(in: .whitespacesAndNewlines)
        let build = (infoDictionary["CFBundleVersion"] as? String)?
            .trimmingCharacters(in: .whitespacesAndNewlines)

        switch (shortVersion, build) {
        case let (version?, build?) where !version.isEmpty && !build.isEmpty:
            return "版本 \(version)（\(build)）"
        case let (version?, _) where !version.isEmpty:
            return "版本 \(version)"
        default:
            return "版本未知"
        }
    }
}

struct AboutView: View {
    let updatesConfigured: Bool
    let onCheckForUpdates: () -> Void

    private var versionText: String {
        AboutInformation.versionText(infoDictionary: Bundle.main.infoDictionary ?? [:])
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                VStack(alignment: .leading, spacing: 4) {
                    Text("关于")
                        .font(.system(size: 25, weight: .semibold))
                    Text("应用信息与版本")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }

                appIdentityCard

                Text("感谢你使用 MiVibe Remote，把遥控器变成更顺手的创作工具。")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding(.vertical, 4)
            }
            .padding(22)
            .frame(maxWidth: 900, alignment: .topLeading)
            .frame(maxWidth: .infinity, alignment: .top)
        }
        .adaptiveSoftTopScrollEdge()
        .background {
            LinearGradient(
                colors: [Color.accentColor.opacity(0.08), Color.clear],
                startPoint: .topLeading,
                endPoint: .center
            )
            .ignoresSafeArea()
        }

    }

    private var appIdentityCard: some View {
        AboutSurface {
            HStack(spacing: 18) {
                Image(nsImage: NSApp.applicationIconImage)
                    .resizable()
                    .scaledToFit()
                    .frame(width: 82, height: 82)
                    .accessibilityLabel("MiVibe Remote 应用图标")

                VStack(alignment: .leading, spacing: 5) {
                    Text(AboutInformation.appName)
                        .font(.system(size: 25, weight: .bold))
                    Text(versionText)
                        .font(.subheadline.monospacedDigit())
                        .foregroundStyle(.secondary)
                }

                Spacer(minLength: 12)

                VStack(alignment: .trailing, spacing: 6) {
                    Button("检查更新…", systemImage: "arrow.triangle.2.circlepath") {
                        onCheckForUpdates()
                    }
                    .adaptiveGlassButtonStyle()
                    .disabled(!updatesConfigured)
                    .help(
                        updatesConfigured
                            ? "使用 Sparkle 检查 MiVibe Remote 更新"
                            : "此安装包未配置自动更新服务"
                    )

                    if !updatesConfigured {
                        Text("自动更新未配置")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }
        }
    }

}

private struct AboutSurface<Content: View>: View {
    private let content: Content

    init(@ViewBuilder content: () -> Content) {
        self.content = content()
    }

    var body: some View {
        content
            .padding(18)
            .adaptiveRegularGlassRounded(cornerRadius: 20)
    }
}

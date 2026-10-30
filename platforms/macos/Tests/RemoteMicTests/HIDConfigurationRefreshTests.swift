import Combine
import Foundation
import Testing
@testable import RemoteMic

@Suite("HID configuration refresh")
struct HIDConfigurationRefreshTests {
    @Test @MainActor func remappingVolumeRefreshesHardwareAfterSettingsCommit() async throws {
        let domain = "MiVibe.HIDRefreshTests.\(UUID().uuidString)"
        let defaults = UserDefaults(suiteName: domain)!
        defer { defaults.removePersistentDomain(forName: domain) }
        let settings = AppSettings(defaults: defaults)
        var mappings: [HIDUsageMapping] = []
        let subscription = settings.hidConfigurationChanges.sink {
            mappings = RemoteKeyHardwareSuppressionPolicy.applying(
                to: [],
                actions: Dictionary(uniqueKeysWithValues: RemoteButton.allCases.map {
                    ($0, settings.action(for: $0))
                }),
                buttonsWithSecondaryActions: []
            )
        }
        defer { subscription.cancel() }
        settings.setAction(.customShortcut, for: .volumeUp)
        settings.setAction(.customShortcut, for: .volumeDown)
        try await Task.sleep(nanoseconds: 200_000_000)
        for button in [RemoteButton.volumeUp, .volumeDown] {
            #expect(mappings.contains(HIDUsageMapping(
                source: RemoteKeyHardwareSuppressionPolicy.usage(button.hidUsage),
                destination: RemoteKeyHardwareSuppressionPolicy.noEventDestination
            )))
        }
        settings.applyCodexPreset()
        try await Task.sleep(nanoseconds: 200_000_000)
        for button in [RemoteButton.volumeUp, .volumeDown] {
            #expect(!mappings.contains {
                $0.source == RemoteKeyHardwareSuppressionPolicy.usage(button.hidUsage)
            })
        }
    }
}

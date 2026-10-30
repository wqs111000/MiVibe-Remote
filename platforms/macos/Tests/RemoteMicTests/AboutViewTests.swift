import Foundation
import Testing
@testable import RemoteMic

@Suite("About page")
struct AboutViewTests {
    @Test func formatsCurrentVersionAndBuildWithoutInventingValues() {
        #expect(AboutInformation.versionText(infoDictionary: [
            "CFBundleShortVersionString": "0.1.10",
            "CFBundleVersion": "11",
        ]) == "版本 0.1.10（11）")
        #expect(AboutInformation.versionText(infoDictionary: [
            "CFBundleShortVersionString": "0.1.10",
        ]) == "版本 0.1.10")
        #expect(AboutInformation.versionText(infoDictionary: [:]) == "版本未知")
    }

}

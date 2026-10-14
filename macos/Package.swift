// swift-tools-version:5.7
import PackageDescription

let package = Package(
    name: "MihomoTray",
    platforms: [
        .macOS(.v12)
    ],
    products: [
        .executable(name: "MihomoTray", targets: ["MihomoTray"])
    ],
    targets: [
        .executableTarget(
            name: "MihomoTray",
            path: "Sources/MihomoTray",
            exclude: [],
            linkerSettings: [
                .linkedFramework("AppKit"),
                .linkedFramework("Foundation")
            ]
        )
    ]
)

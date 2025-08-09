import os
import requests
from anythingllm_api import get_anythingllm_files


ANYTHINGLLM_API_KEY = os.getenv("ANYTHINGLLM_API_KEY")

def upload_link(link, json_data):
    url = f"http://localhost:3001/api/v1/document/upload-link"
    headers = {
        "Authorization": f"Bearer {ANYTHINGLLM_API_KEY}",
        "Accept": "application/json"
    }

    print(f"scraping site {link}")
    response = requests.post(url, headers=headers, json=json_data)
    print(f"scrape status code: {response.status_code}")
    if response.status_code == 200:
        return True
    return False

dotnet_maui_links = [
    "https://learn.microsoft.com/en-us/dotnet/maui/?view=net-maui-9.0",
    "https://learn.microsoft.com/en-us/dotnet/api/?view=net-maui-9.0&preserve-view=true",
    "https://learn.microsoft.com/en-us/dotnet/core/whats-new/dotnet-9/overview",
    "https://learn.microsoft.com/en-us/dotnet/core/whats-new/dotnet-9/sdk",
    "https://learn.microsoft.com/en-us/dotnet/fundamentals/",
    "https://learn.microsoft.com/en-us/dotnet/api/?view=net-9.0",
    "https://learn.microsoft.com/en-us/dotnet/api/?view=net-maui-9.0",
    "https://github.com/dotnet/maui/releases",
    "https://devblogs.microsoft.com/dotnet/category/maui/",
    "https://amarozka.dev/whats-new-dotnet-maui-2025/",
    "https://www.telerik.com/maui-ui/resources",
    "https://github.com/jsuarezruiz/awesome-dotnet-maui",
    "https://github.com/jfversluis/built-with-maui",
    "https://github.com/jfversluis/learn-dotnet-maui",
    "https://github.com/jsuarezruiz/dotnet-maui-showcase",
    "https://learn.microsoft.com/en-us/dotnet/maui/get-started/resources?view=net-maui-9.0",
    "https://learn.microsoft.com/en-us/dotnet/maui/fundamentals/?view=net-maui-9.0",
    "https://learn.microsoft.com/en-us/dotnet/maui/user-interface/?view=net-maui-9.0",
    "https://learn.microsoft.com/en-us/dotnet/maui/data-cloud/?view=net-maui-9.0",
    "https://learn.microsoft.com/en-us/dotnet/maui/fundamentals/data-binding/?view=net-maui-9.0",
    "https://learn.microsoft.com/en-us/dotnet/architecture/maui/",
    "https://learn.microsoft.com/en-us/dotnet/maui/fundamentals/dependency-injection/?view=net-maui-9.0",
    "https://learn.microsoft.com/en-us/dotnet/maui/platform-integration/?view=net-maui-9.0",
    "https://learn.microsoft.com/en-us/dotnet/maui/platform-integration/device-media/speech-recognition?view=net-maui-9.0",
    "https://learn.microsoft.com/en-us/dotnet/maui/data-cloud/database/sqlite?view=net-maui-9.0",
    "https://learn.microsoft.com/en-us/dotnet/maui/platform-integration/storage/secure-storage?view=net-maui-9.0",
    "https://learn.microsoft.com/en-us/azure/developer/mobile-apps/azure-mobile-apps/quickstarts/maui/",
    "https://learn.microsoft.com/en-us/dotnet/maui/data-cloud/rest?view=net-maui-9.0",
    "https://learn.microsoft.com/en-us/dotnet/maui/data-cloud/authentication/?view=net-maui-9.0",
    "https://learn.microsoft.com/en-us/dotnet/maui/deployment/?view=net-maui-9.0",
    "https://learn.microsoft.com/en-us/dotnet/maui/fundamentals/app-lifecycle?view=net-maui-9.0",
    "https://www.nuget.org/packages?q=maui",  # Package discovery
    "https://github.com/CommunityToolkit/Maui",  # Community toolkit
    "https://www.syncfusion.com/maui-controls",  # UI components
    "https://www.syncfusion.com/blogs/post/syncfusion-open-source-net-maui-controls-cross-platform",
    "https://learn.microsoft.com/en-us/aspnet/core/blazor/hybrid/?view=aspnetcore-9.0",
    "https://learn.microsoft.com/en-us/aspnet/core/blazor/hybrid/tutorials/maui?view=aspnetcore-9.0",
    "https://learn.microsoft.com/en-us/aspnet/core/blazor/?view=aspnetcore-9.0",
    "https://learn.microsoft.com/en-us/aspnet/core/blazor/components/?view=aspnetcore-9.0",
    "https://learn.microsoft.com/en-us/aspnet/core/blazor/data-binding?view=aspnetcore-9.0",
    "https://learn.microsoft.com/en-us/dotnet/maui/user-interface/controls/blazorwebview?view=net-maui-9.0",
    "https://learn.microsoft.com/en-us/aspnet/core/blazor/hybrid/security/?view=aspnetcore-9.0",
    "https://learn.microsoft.com/en-us/aspnet/core/blazor/javascript-interoperability/?view=aspnetcore-9.0",
    "https://learn.microsoft.com/en-us/aspnet/core/blazor/javascript-interoperability/call-javascript-from-dotnet?view=aspnetcore-9.0",
    "https://learn.microsoft.com/en-us/aspnet/core/blazor/state-management?view=aspnetcore-9.0",
    "https://learn.microsoft.com/en-us/aspnet/core/blazor/fundamentals/dependency-injection?view=aspnetcore-9.0",
    "https://github.com/AdrienTorris/awesome-blazor",
    "https://blazor.net/",
    "https://www.telerik.com/blazor-ui",
    "https://mudblazor.com/",
    "https://learn.microsoft.com/en-us/dotnet/maui/platform-integration/?view=net-maui-9.0",
    "https://learn.microsoft.com/en-us/dotnet/maui/platform-integration/device/?view=net-maui-9.0",
    "https://learn.microsoft.com/en-us/dotnet/communitytoolkit/introduction",
    "https://learn.microsoft.com/en-us/dotnet/communitytoolkit/maui/",
    "https://github.com/CommunityToolkit/Maui",
    "https://learn.microsoft.com/en-us/dotnet/communitytoolkit/maui/behaviors/",
    "https://learn.microsoft.com/en-us/dotnet/communitytoolkit/maui/converters/",
    "https://learn.microsoft.com/en-us/dotnet/communitytoolkit/maui/markup/markup",
    "https://github.com/jamesmontemagno/MediaPlugin",  # Camera/Media
    "https://github.com/jamesmontemagno/ConnectivityPlugin",  # Network
    "https://github.com/CrossGeeks/PermissionsPlugin",  # Permissions
    "https://github.com/jamesmontemagno/SettingsPlugin",  # Settings storage
    "https://learn.microsoft.com/en-us/dotnet/maui/platform-integration/invoke-platform-code?view=net-maui-9.0",
    "https://devblogs.microsoft.com/dotnet/introducing-net-multi-platform-app-ui-maui/",
    "https://www.nuget.org/packages?q=Tags%3A%22maui%22",
    "https://www.nuget.org/packages?q=Tags%3A%22dotnet-maui%22",
    "https://mudblazor.com/",  # Material Design components
    "https://blazorise.com/",  # Bootstrap components
    "https://www.radzen.com/blazor-components/",  # Radzen components
    "https://www.telerik.com/blazor-ui",  # Telerik UI for Blazor
    "https://www.syncfusion.com/blazor-components",  # Syncfusion
    "https://learn.microsoft.com/en-us/aspnet/core/blazor/javascript-interoperability/?view=aspnetcore-9.0",
    "https://learn.microsoft.com/en-us/aspnet/core/blazor/javascript-interoperability/import-export-interop?view=aspnetcore-9.0",
    "https://www.nuget.org/packages?q=blazor",
    "https://github.com/AdrienTorris/awesome-blazor#libraries--extensions",
    "https://learn.microsoft.com/en-us/aspnet/core/blazor/components/?view=aspnetcore-9.0",
    "https://learn.microsoft.com/en-us/aspnet/core/blazor/components/libraries?view=aspnetcore-9.0",
    "https://learn.microsoft.com/en-us/dotnet/maui/user-interface/animation/basic?view=net-maui-9.0",
    "https://learn.microsoft.com/en-us/dotnet/maui/user-interface/animation/custom?view=net-maui-9.0",
    "https://learn.microsoft.com/en-us/dotnet/maui/user-interface/animation/easing?view=net-maui-9.0",
    "https://learn.microsoft.com/en-us/dotnet/maui/user-interface/visual-states?view=net-maui-9.0",
    "https://learn.microsoft.com/en-us/dotnet/maui/user-interface/brushes/?view=net-maui-9.0",
    "https://learn.microsoft.com/en-us/dotnet/maui/user-interface/visual-states?view=net-maui-9.0",
    "https://learn.microsoft.com/en-us/dotnet/maui/user-interface/brushes/?view=net-maui-9.0",
    "https://github.com/jsuarezruiz/netmaui-animation-samples",
    "https://devblogs.microsoft.com/dotnet/announcing-dotnet-maui-community-toolkit/",
    "https://github.com/Baseflow/LottieXamarin",  # Works with MAUI
    "https://www.nuget.org/packages/SkiaSharp.Extended.UI.Maui/",  # Lottie support
    "https://learn.microsoft.com/en-us/aspnet/core/blazor/components/css-isolation?view=aspnetcore-9.0",
    "https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Animations",
    "https://animate.style/",  # Popular CSS animation library
    "https://learn.microsoft.com/en-us/aspnet/core/blazor/javascript-interoperability/call-javascript-from-dotnet?view=aspnetcore-9.0",
    "https://greensock.com/gsap/",  # GSAP animations (via JS interop)
    "https://animejs.com/",  # Anime.js (via JS interop)
    "https://github.com/Garderoben/MudBlazor.Extensions",  # MudBlazor extensions with animations
    "https://blazorise.com/docs/components/animate",  # Blazorise animations
    "https://css-tricks.com/almanac/properties/a/animation/",
    "https://www.framer.com/motion/",  # Concepts applicable via JS interop
    "https://lottiefiles.com/",  # Main Lottie resource hub
    "https://airbnb.design/lottie/",  # Official Lottie documentation
    "https://lottiefiles.com/featured",  # Featured animations for inspiration
    "https://github.com/Baseflow/LottieXamarin",  # Primary Lottie for MAUI
    "https://www.nuget.org/packages/Lottie.Forms/",  # Lottie Forms package
    "https://github.com/martijn00/LottieXamarin/wiki",  # Implementation guide
    "https://github.com/mono/SkiaSharp.Extended",  # SkiaSharp Lottie support
    "https://www.nuget.org/packages/SkiaSharp.Extended.UI.Maui/",  # MAUI SkiaSharp
    "https://github.com/Keyyl/Blazor.Lottie",  # Blazor Lottie wrapper
    "https://www.npmjs.com/package/lottie-web",  # Web Lottie (for JS interop)
    "https://github.com/airbnb/lottie-web",  # Official web implementation
    "https://www.adobe.com/products/aftereffects.html",  # After Effects export
    "https://aescripts.com/bodymovin/",  # After Effects Bodymovin plugin
    "https://lottiefiles.com/tools/lottie-creator",  # Online Lottie creator
    "https://learn.microsoft.com/en-us/dotnet/maui/user-interface/controls/create-custom-controls?view=net-maui-9.0",
    "https://learn.microsoft.com/en-us/dotnet/maui/user-interface/handlers/?view=net-maui-9.0",
    "https://learn.microsoft.com/en-us/dotnet/maui/user-interface/handlers/create?view=net-maui-9.0",
    "https://github.com/jsuarezruiz/netmaui-controls-gallery",  # Control examples
    "https://github.com/dotnet/Microsoft.Maui.Graphics",  # Custom drawing
    "https://learn.microsoft.com/en-us/dotnet/maui/user-interface/graphics/?view=net-maui-9.0",
    "https://github.com/jsuarezruiz/AlohaKit.Controls",  # AlohaKit controls
    "https://github.com/FreakyAli/Maui.FreakyControls",  # FreakyControls
    "https://github.com/VladislavAntonyuk/MauiSamples",  # Advanced samples
    "https://learn.microsoft.com/en-us/dotnet/maui/user-interface/controls/controltemplate?view=net-maui-9.0",
    "https://learn.microsoft.com/en-us/dotnet/maui/user-interface/styles/?view=net-maui-9.0",
    "https://learn.microsoft.com/en-us/dotnet/maui/user-interface/theming?view=net-maui-9.0",
    "https://learn.microsoft.com/en-us/aspnet/core/blazor/components/?view=aspnetcore-9.0",
    "https://learn.microsoft.com/en-us/aspnet/core/blazor/components/templated-components?view=aspnetcore-9.0",
    "https://learn.microsoft.com/en-us/aspnet/core/blazor/components/generic-type-support?view=aspnetcore-9.0",
    "https://learn.microsoft.com/en-us/aspnet/core/blazor/components/cascading-values-and-parameters?view=aspnetcore-9.0",
    "https://learn.microsoft.com/en-us/aspnet/core/blazor/components/event-handling?view=aspnetcore-9.0",
    "https://learn.microsoft.com/en-us/aspnet/core/blazor/components/rendering?view=aspnetcore-9.0",
    "https://github.com/MudBlazor/MudBlazor",  # MudBlazor source
    "https://github.com/Megabit/Blazorise",  # Blazorise source
    "https://github.com/radzenhq/radzen-blazor",  # Radzen source
    "https://learn.microsoft.com/en-us/aspnet/core/blazor/components/css-isolation?view=aspnetcore-9.0",
    "https://sass-lang.com/documentation/",  # SCSS for advanced styling
    "https://learn.microsoft.com/en-us/dotnet/communitytoolkit/",
    "https://learn.microsoft.com/en-us/dotnet/communitytoolkit/maui/",
    "https://learn.microsoft.com/en-us/dotnet/communitytoolkit/mvvm/",
    "https://github.com/CommunityToolkit/dotnet",
    "https://learn.microsoft.com/en-us/dotnet/communitytoolkit/maui/behaviors/",
    "https://learn.microsoft.com/en-us/dotnet/communitytoolkit/maui/converters/",
    "https://learn.microsoft.com/en-us/dotnet/communitytoolkit/maui/extensions/",
    "https://learn.microsoft.com/en-us/dotnet/communitytoolkit/maui/views/",
    "https://www.syncfusion.com/maui-controls",  # Syncfusion MAUI
    "https://github.com/syncfusion/maui-toolkit",
    "https://github.com/jsuarezruiz/TemplateMAUI",
    "https://www.telerik.com/maui-ui",  # Telerik MAUI
    "https://www.devexpress.com/maui/",  # DevExpress MAUI
    "https://github.com/xceedsoftware/Xceed-Toolkit-for-.NET-MAUI",
    "https://github.com/DevExpress/maui-demo-app",  # DevExpress samples
    "https://m3.material.io/",  # Material Design 3
    "https://learn.microsoft.com/en-us/dotnet/maui/user-interface/material-design?view=net-maui-9.0",
    "https://github.com/MaterialDesignInXAML/MaterialDesignInXamlToolkit",
    "https://github.com/berkaroad/RichTextKit",  # Rich text for MAUI
    "https://quilljs.com/",  # Quill editor (Blazor JS interop)
    "https://www.tiny.cloud/",  # TinyMCE (Blazor JS interop)
    "https://lottiefiles.com/search?q=microphone&category=animations",  # Voice animations
    "https://lottiefiles.com/search?q=recording&category=animations",  # Recording animations
    "https://lottiefiles.com/search?q=book&category=animations",  # Book animations
    "https://lottiefiles.com/search?q=spiritual&category=animations",  # Spiritual themes
    "https://learn.microsoft.com/en-us/aspnet/core/blazor/hybrid/class-libraries?view=aspnetcore-9.0",
    "https://learn.microsoft.com/en-us/aspnet/core/blazor/hybrid/developer-tools?view=aspnetcore-9.0",
    "https://learn.microsoft.com/en-us/aspnet/core/blazor/progressive-web-app?view=aspnetcore-9.0",
    "https://learn.microsoft.com/en-us/aspnet/core/blazor/hybrid/routing?view=aspnetcore-9.0",
    "https://learn.microsoft.com/en-us/aspnet/core/blazor/file-uploads?view=aspnetcore-9.0",
    "https://learn.microsoft.com/en-us/aspnet/core/blazor/forms/?view=aspnetcore-9.0",
    "https://github.com/dotnet/aspnetcore/tree/main/src/Components/samples",
    "https://github.com/dotnet/maui/wiki/Known-Issues",
    "https://learn.microsoft.com/en-us/dotnet/maui/troubleshooting?view=net-maui-9.0",
    "https://github.com/dotnet/maui/issues?q=is%3Aissue+label%3Abug+is%3Aclosed",
    "https://learn.microsoft.com/en-us/aspnet/core/blazor/fundamentals/logging?view=aspnetcore-9.0",
    "https://learn.microsoft.com/en-us/aspnet/core/blazor/fundamentals/handle-errors?view=aspnetcore-9.0",
    "https://github.com/dotnet/aspnetcore/issues?q=blazor+is%3Aclosed+label%3Abug",
    "https://learn.microsoft.com/en-us/dotnet/maui/troubleshooting/performance?view=net-maui-9.0",
    "https://learn.microsoft.com/en-us/aspnet/core/blazor/performance?view=aspnetcore-9.0",
    "https://github.com/dotnet/maui/discussions/2720",  # Rich text discussions
    "https://learn.microsoft.com/en-us/dotnet/maui/user-interface/controls/editor?view=net-maui-9.0",
    "https://github.com/CommunityToolkit/Maui/discussions/categories/feature-requests",
    "https://github.com/search?q=bible+maui&type=repositories",  # Bible app examples
    "https://github.com/search?q=devotional+blazor&type=repositories",  # Devotional apps
    "https://learn.microsoft.com/en-us/azure/ai-services/language-service/key-phrase-extraction/overview",
    "https://learn.microsoft.com/en-us/azure/ai-services/language-service/sentiment-opinion-mining/overview",
    "https://github.com/Azure-Samples/cognitive-services-dotnet-sdk-samples",
    "https://learn.microsoft.com/en-us/aspnet/core/signalr/introduction?view=aspnetcore-9.0",
    "https://github.com/aspnet/SignalR-samples",
    "https://learn.microsoft.com/en-us/dotnet/maui/data-cloud/azure-signalr?view=net-maui-9.0",
    "https://github.com/jsuarezruiz/netmaui-ui-challenges",  # UI challenges
    "https://github.com/jsuarezruiz/netmaui-beautiful-ui",   # Beautiful UI samples
    "https://github.com/dotnet/maui-samples",  # Official samples
    "https://github.com/dotnet-presentations/blazor-workshop/tree/main/docs",
    "https://blazor.radzen.com/",  # Interactive demos
    "https://try.mudblazor.com/",  # MudBlazor demos
    "https://github.com/unoplatform/Uno.Samples",  # Cross-platform UI patterns
    "https://github.com/VladislavAntonyuk/MauiSamples/tree/main/MauiAnimations",
    "https://dotnet.microsoft.com/en-us/learn/videos",
    "https://learn.microsoft.com/en-us/training/modules/build-blazor-hybrid/",
    "https://learn.microsoft.com/en-us/training/paths/build-apps-with-dotnet-maui/",
    "https://github.com/dotnet-presentations/blazor-hybrid-workshop",
    "https://github.com/dotnet-presentations/dotnet-maui-workshop",
]

flutter_links = [
    "https://docs.flutter.dev/",
    "https://api.flutter.dev",
    "https://dart.dev/language/async",
    "https://dart.dev/language",
    "https://dart.dev/docs",
    "https://medium.com/@emanyaqoob/flutter-state-management-choosing-the-right-approach-64b2ccf59235",
    "https://www.f22labs.com/blogs/state-management-in-flutter-7-approaches-to-know-2025/",
    "https://www.geeksforgeeks.org/flutter/how-to-choose-the-right-architecture-pattern-for-your-flutter-app/",
    #"https://www.geeksforgreeks.org/flutter/implementing-rest-api-in-flutter/",
    "https://medium.com/@yusrasajjad613/architecture-patterns-in-flutter-an-in-depth-guide-0ca2d65c723c",
    "https://www.geeksforgeeks.org/flutter/ways-to-optimize-the-performance-of-your-flutter-application/",
    "https://dev.to/nithya_iyer/flutter-performance-optimization-best-practices-for-faster-apps-3dcd",
    "https://www.headspin.io/blog/flutter-testing-guide",
    "https://dev.to/misterankit/the-comprehensive-guide-to-flutter-app-testing-best-practices-and-proven-strategies-51m8",
    "https://verygood.ventures/blog",
    "https://firebase.flutter.dev",
    "https://github.com/flutter/samples",
    "https://docs.flutter.dev/ui/animations",  # Better than community blogs
    "https://docs.flutter.dev/cookbook",       # Practical recipes
    "https://flutter.dev/showcase",            # Real-world examples
    "https://github.com/flutter/gallery",     # Material Gallery source
    "https://docs.flutter.dev/perf",          # Performance guidance
]

azure_links = [
    "https://learn.microsoft.com/en-us/azure/ai-services/",
    "https://learn.microsoft.com/en-us/azure/ai-services/openai/",
    "https://learn.microsoft.com/en-us/azure/ai-services/language-service/",
    "https://learn.microsoft.com/en-us/azure/ai-services/speech-service/",
    "https://learn.microsoft.com/en-us/azure/storage/blobs/",
    "https://learn.microsoft.com/en-us/azure/active-directory-b2c/",
    "https://learn.microsoft.com/en-us/azure/active-directory-b2c/identity-provider-google",
    "https://learn.microsoft.com/en-us/azure/active-directory-b2c/identity-provider-facebook",
    "https://learn.microsoft.com/en-us/azure/active-directory-b2c/identity-provider-apple",
    "https://learn.microsoft.com/en-us/entra/external-id/",
    "https://learn.microsoft.com/en-us/azure/cosmos-db/",  # NoSQL database for notes/themes
    "https://learn.microsoft.com/en-us/azure/functions/",  # Serverless backend functions
    "https://learn.microsoft.com/en-us/azure/notification-hubs/",  # Push notifications for friend sharing
    "https://learn.microsoft.com/en-us/azure/cognitive-services/text-analytics/",  # Theme extraction
    "https://learn.microsoft.com/en-us/azure/app-service/",  # Backend hosting
    "https://learn.microsoft.com/en-us/azure/search/"  # For biblical cross-referencing search
]

other_links = [
    "https://pub.dev/",
    "https://pub.dev/packages/flutter_riverpod",
    "https://pub.dev/packages/speech_to_text",
    "https://pub.dev/packages/provider",
    "https://pub.dev/packages/bloc",      # BLoC pattern documentation
    "https://docs.flutter.dev/ui/navigation",  # Navigation patterns
    "https://docs.flutter.dev/data-and-backend/networking",  # HTTP/API integration
    "https://docs.flutter.dev/platform-integration/platform-channels",  # Platform-specific code
    "https://docs.flutter.dev/security",  # Security best practices
    "https://pub.dev/packages/sqflite",    # Local database
    "https://pub.dev/packages/shared_preferences",  # Local storage
    "https://pub.dev/packages/http",       # HTTP requests
    "https://pub.dev/packages/flutter_secure_storage",  # Secure token storage
    "https://pub.dev/packages/permission_handler",  # Microphone permissions
    "https://pub.dev/packages/connectivity_plus",   # Network connectivity
    "https://biblehub.com/",               # Biblical reference data
    "https://www.crosswire.org/sword/",    # Bible software libraries
    "https://pub.dev/packages/sqflite"    # Local database
]

all_links = dotnet_maui_links + flutter_links + azure_links + other_links

uploaded_urls = get_anythingllm_files("custom-documents")
#print(len(uploaded_urls["documents"]))
#print(uploaded_urls["documents"][0])
for link in all_links:
    link_match = False
    for doc in uploaded_urls["documents"]:
        if doc["chunkSource"] == f"link://{link}":
            print(f"exists: {link}")
            link_match = True
            break
    
    if link_match:
        continue

    print(f"\nnew link: {link}")

    data = {
        "link": link,
        "addToWorkspaces": "test,selos-main,selos-development,selos-experiments"
    }
    print(f"    - uploading: {link})")
    upload_link(link, data)
    print('\n')

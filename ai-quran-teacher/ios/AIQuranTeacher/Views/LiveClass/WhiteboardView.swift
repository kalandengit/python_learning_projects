import SwiftUI

/// Shared whiteboard: local strokes are broadcast over the signaling
/// channel; remote strokes arrive via `.remoteDrawingReceived`.
struct WhiteboardView: View {
    @ObservedObject var viewModel: LiveClassViewModel

    struct Stroke: Identifiable {
        let id = UUID()
        var points: [CGPoint]
        var color: Color
    }

    @State private var strokes: [Stroke] = []
    @State private var currentStroke: Stroke?
    @State private var selectedColor: Color = .primary

    private let palette: [Color] = [.primary, .red, .blue, .green, .orange]

    var body: some View {
        VStack(spacing: 0) {
            Canvas { context, _ in
                for stroke in strokes + (currentStroke.map { [$0] } ?? []) {
                    var path = Path()
                    path.addLines(stroke.points)
                    context.stroke(path, with: .color(stroke.color), lineWidth: 3)
                }
            }
            .background(Color(.systemBackground))
            .gesture(
                DragGesture(minimumDistance: 0)
                    .onChanged { value in
                        if currentStroke == nil {
                            currentStroke = Stroke(points: [], color: selectedColor)
                        }
                        currentStroke?.points.append(value.location)
                    }
                    .onEnded { _ in
                        guard let stroke = currentStroke else { return }
                        strokes.append(stroke)
                        viewModel.sendDrawing(
                            points: stroke.points,
                            color: selectedColor.description
                        )
                        currentStroke = nil
                    }
            )

            HStack(spacing: 16) {
                ForEach(palette, id: \.self) { color in
                    Circle()
                        .fill(color)
                        .frame(width: 26, height: 26)
                        .overlay(
                            Circle().stroke(Color.accentColor,
                                            lineWidth: selectedColor == color ? 3 : 0)
                        )
                        .onTapGesture { selectedColor = color }
                }
                Spacer()
                Button {
                    strokes.removeAll()
                } label: {
                    Image(systemName: "trash")
                }
            }
            .padding()
            .background(.bar)
        }
        .onReceive(NotificationCenter.default.publisher(for: .remoteDrawingReceived)) { notification in
            guard let drawing = notification.object as? [String: Any],
                  let rawPoints = drawing["points"] as? [[String: CGFloat]] else { return }
            let points = rawPoints.compactMap { dict -> CGPoint? in
                guard let x = dict["x"], let y = dict["y"] else { return nil }
                return CGPoint(x: x, y: y)
            }
            strokes.append(Stroke(points: points, color: .blue))
        }
    }
}

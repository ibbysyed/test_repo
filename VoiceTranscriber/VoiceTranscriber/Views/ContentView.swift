import SwiftUI

struct ContentView: View {
    @StateObject private var audioManager = AudioRecorderManager()
    @StateObject private var config = Config.shared
    @State private var showingPermissionAlert = false
    @State private var showingSettings = false
    @State private var hasPermission = false

    var body: some View {
        NavigationView {
            VStack {
                if !config.isConfigured {
                    ConfigurationWarningView(showSettings: $showingSettings)
                }

                RecordingControlView(audioManager: audioManager, hasPermission: $hasPermission)
                    .padding()

                Divider()

                RecordingsListView(audioManager: audioManager)
            }
            .navigationTitle("Voice Transcriber")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        showingSettings = true
                    }) {
                        Image(systemName: "gear")
                    }
                }
            }
            .sheet(isPresented: $showingSettings) {
                SettingsView()
            }
            .onAppear {
                checkPermissions()
            }
            .alert("Microphone Permission Required", isPresented: $showingPermissionAlert) {
                Button("OK") { }
            } message: {
                Text("Please enable microphone access in Settings to record audio.")
            }
        }
    }

    private func checkPermissions() {
        audioManager.requestPermission { granted in
            hasPermission = granted
            if !granted {
                showingPermissionAlert = true
            }
        }
    }
}

struct ConfigurationWarningView: View {
    @Binding var showSettings: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundColor(.orange)
                Text("Configuration Required")
                    .font(.headline)
            }
            Text("Configure your OpenAI and Snowflake credentials to start transcribing and uploading recordings.")
                .font(.caption)
                .foregroundColor(.secondary)

            Button(action: {
                showSettings = true
            }) {
                HStack {
                    Image(systemName: "gear")
                    Text("Open Settings")
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 8)
            }
            .buttonStyle(.bordered)
        }
        .padding()
        .background(Color.orange.opacity(0.1))
        .cornerRadius(8)
        .padding(.horizontal)
    }
}

struct RecordingControlView: View {
    @ObservedObject var audioManager: AudioRecorderManager
    @Binding var hasPermission: Bool

    var body: some View {
        VStack(spacing: 20) {
            if audioManager.isRecording {
                Text(formatDuration(audioManager.currentRecordingDuration))
                    .font(.system(size: 48, weight: .bold, design: .monospaced))
                    .foregroundColor(.red)
            }

            Button(action: {
                if audioManager.isRecording {
                    audioManager.stopRecording()
                } else {
                    if hasPermission {
                        audioManager.startRecording()
                    }
                }
            }) {
                ZStack {
                    Circle()
                        .fill(audioManager.isRecording ? Color.red : Color.blue)
                        .frame(width: 80, height: 80)

                    if audioManager.isRecording {
                        RoundedRectangle(cornerRadius: 8)
                            .fill(Color.white)
                            .frame(width: 30, height: 30)
                    } else {
                        Circle()
                            .fill(Color.white)
                            .frame(width: 30, height: 30)
                    }
                }
            }
            .disabled(!hasPermission)

            Text(audioManager.isRecording ? "Tap to Stop" : "Tap to Record")
                .font(.caption)
                .foregroundColor(.secondary)
        }
    }

    private func formatDuration(_ duration: TimeInterval) -> String {
        let minutes = Int(duration) / 60
        let seconds = Int(duration) % 60
        let milliseconds = Int((duration.truncatingRemainder(dividingBy: 1)) * 10)
        return String(format: "%02d:%02d.%01d", minutes, seconds, milliseconds)
    }
}

struct RecordingsListView: View {
    @ObservedObject var audioManager: AudioRecorderManager

    var body: some View {
        List {
            ForEach(audioManager.recordings.reversed()) { recording in
                NavigationLink(destination: RecordingDetailView(recording: recording, audioManager: audioManager)) {
                    RecordingRowView(recording: recording)
                }
            }
            .onDelete { indexSet in
                let reversedRecordings = audioManager.recordings.reversed()
                for index in indexSet {
                    let recording = reversedRecordings[index]
                    audioManager.deleteRecording(recording)
                }
            }
        }
        .listStyle(.plain)
    }
}

struct RecordingRowView: View {
    let recording: Recording

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(formatDate(recording.date))
                    .font(.headline)
                Spacer()
                if recording.uploadedToSnowflake {
                    Image(systemName: "checkmark.cloud.fill")
                        .foregroundColor(.green)
                }
            }

            Text("Duration: \(formatDuration(recording.duration))")
                .font(.caption)
                .foregroundColor(.secondary)

            if let transcription = recording.transcription {
                Text(transcription)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(2)
            } else {
                Text("Not transcribed")
                    .font(.caption)
                    .foregroundColor(.orange)
                    .italic()
            }
        }
        .padding(.vertical, 4)
    }

    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter.string(from: date)
    }

    private func formatDuration(_ duration: TimeInterval) -> String {
        let minutes = Int(duration) / 60
        let seconds = Int(duration) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
}

#Preview {
    ContentView()
}

import SwiftUI

struct RecordingDetailView: View {
    let recording: Recording
    @ObservedObject var audioManager: AudioRecorderManager
    @ObservedObject private var config = Config.shared

    @State private var isTranscribing = false
    @State private var isUploading = false
    @State private var errorMessage: String?
    @State private var showError = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                // Recording Info
                VStack(alignment: .leading, spacing: 8) {
                    Text("Recording Info")
                        .font(.headline)

                    InfoRow(label: "Date", value: formatDate(recording.date))
                    InfoRow(label: "Duration", value: formatDuration(recording.duration))
                    InfoRow(label: "Filename", value: recording.filename)
                }
                .padding()
                .background(Color(.systemGray6))
                .cornerRadius(12)

                // Playback Controls
                VStack(spacing: 12) {
                    Button(action: {
                        audioManager.playRecording(recording)
                    }) {
                        HStack {
                            Image(systemName: "play.circle.fill")
                            Text("Play Recording")
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.blue)
                        .foregroundColor(.white)
                        .cornerRadius(10)
                    }

                    Button(action: {
                        audioManager.stopPlaying()
                    }) {
                        HStack {
                            Image(systemName: "stop.circle.fill")
                            Text("Stop")
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.gray)
                        .foregroundColor(.white)
                        .cornerRadius(10)
                    }
                }

                Divider()

                // Transcription Section
                VStack(alignment: .leading, spacing: 12) {
                    Text("Transcription")
                        .font(.headline)

                    if let transcription = recording.transcription {
                        Text(transcription)
                            .padding()
                            .background(Color(.systemGray6))
                            .cornerRadius(8)
                    } else {
                        Text("No transcription available")
                            .foregroundColor(.secondary)
                            .italic()
                    }

                    Button(action: {
                        transcribeRecording()
                    }) {
                        HStack {
                            if isTranscribing {
                                ProgressView()
                                    .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                Text("Transcribing...")
                            } else {
                                Image(systemName: "waveform.circle.fill")
                                Text(recording.transcription == nil ? "Transcribe with OpenAI" : "Re-transcribe")
                            }
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(isTranscribing ? Color.gray : Color.green)
                        .foregroundColor(.white)
                        .cornerRadius(10)
                    }
                    .disabled(isTranscribing || !config.isConfigured)
                }

                Divider()

                // Upload Section
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Text("Upload to Snowflake")
                            .font(.headline)
                        Spacer()
                        if recording.uploadedToSnowflake {
                            HStack {
                                Image(systemName: "checkmark.circle.fill")
                                    .foregroundColor(.green)
                                Text("Uploaded")
                                    .font(.caption)
                                    .foregroundColor(.green)
                            }
                        }
                    }

                    Button(action: {
                        uploadToSnowflake()
                    }) {
                        HStack {
                            if isUploading {
                                ProgressView()
                                    .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                Text("Uploading...")
                            } else {
                                Image(systemName: "cloud.fill")
                                Text(recording.uploadedToSnowflake ? "Re-upload" : "Upload to Snowflake")
                            }
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(isUploading ? Color.gray : Color.purple)
                        .foregroundColor(.white)
                        .cornerRadius(10)
                    }
                    .disabled(isUploading || recording.transcription == nil || !config.isConfigured)

                    if recording.transcription == nil {
                        Text("Transcribe the recording first before uploading")
                            .font(.caption)
                            .foregroundColor(.orange)
                    }
                }
            }
            .padding()
        }
        .navigationTitle("Recording Details")
        .navigationBarTitleDisplayMode(.inline)
        .alert("Error", isPresented: $showError) {
            Button("OK") { }
        } message: {
            Text(errorMessage ?? "An unknown error occurred")
        }
    }

    private func transcribeRecording() {
        isTranscribing = true
        errorMessage = nil

        Task {
            do {
                let url = audioManager.getRecordingURL(for: recording)
                let transcription = try await OpenAIService.shared.transcribeAudio(fileURL: url)

                var updatedRecording = recording
                updatedRecording.transcription = transcription
                audioManager.updateRecording(updatedRecording)

                await MainActor.run {
                    isTranscribing = false
                }
            } catch {
                await MainActor.run {
                    isTranscribing = false
                    errorMessage = error.localizedDescription
                    showError = true
                }
            }
        }
    }

    private func uploadToSnowflake() {
        isUploading = true
        errorMessage = nil

        Task {
            do {
                try await SnowflakeService.shared.uploadTranscription(recording: recording)

                var updatedRecording = recording
                updatedRecording.uploadedToSnowflake = true
                audioManager.updateRecording(updatedRecording)

                await MainActor.run {
                    isUploading = false
                }
            } catch {
                await MainActor.run {
                    isUploading = false
                    errorMessage = error.localizedDescription
                    showError = true
                }
            }
        }
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

struct InfoRow: View {
    let label: String
    let value: String

    var body: some View {
        HStack {
            Text(label)
                .foregroundColor(.secondary)
            Spacer()
            Text(value)
                .bold()
        }
    }
}

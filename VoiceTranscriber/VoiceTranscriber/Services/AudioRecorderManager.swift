import Foundation
import AVFoundation

class AudioRecorderManager: NSObject, ObservableObject {
    @Published var isRecording = false
    @Published var recordings: [Recording] = []
    @Published var currentRecordingDuration: TimeInterval = 0

    private var audioRecorder: AVAudioRecorder?
    private var audioPlayer: AVAudioPlayer?
    private var recordingTimer: Timer?
    private var currentRecordingStartTime: Date?

    override init() {
        super.init()
        loadRecordings()
        setupAudioSession()
    }

    private func setupAudioSession() {
        let audioSession = AVAudioSession.sharedInstance()
        do {
            try audioSession.setCategory(.playAndRecord, mode: .default)
            try audioSession.setActive(true)
        } catch {
            print("Failed to set up audio session: \(error)")
        }
    }

    func requestPermission(completion: @escaping (Bool) -> Void) {
        AVAudioSession.sharedInstance().requestRecordPermission { allowed in
            DispatchQueue.main.async {
                completion(allowed)
            }
        }
    }

    func startRecording() {
        let filename = "recording_\(Date().timeIntervalSince1970).m4a"
        let path = getDocumentsDirectory().appendingPathComponent(filename)

        let settings: [String: Any] = [
            AVFormatIDKey: Int(kAudioFormatMPEG4AAC),
            AVSampleRateKey: 44100.0,
            AVNumberOfChannelsKey: 2,
            AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue
        ]

        do {
            audioRecorder = try AVAudioRecorder(url: path, settings: settings)
            audioRecorder?.delegate = self
            audioRecorder?.record()

            isRecording = true
            currentRecordingStartTime = Date()
            currentRecordingDuration = 0

            // Start timer to update duration
            recordingTimer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { [weak self] _ in
                guard let self = self,
                      let startTime = self.currentRecordingStartTime else { return }
                self.currentRecordingDuration = Date().timeIntervalSince(startTime)
            }
        } catch {
            print("Failed to start recording: \(error)")
        }
    }

    func stopRecording() {
        audioRecorder?.stop()
        isRecording = false
        recordingTimer?.invalidate()
        recordingTimer = nil

        if let url = audioRecorder?.url {
            let filename = url.lastPathComponent
            let recording = Recording(
                filename: filename,
                date: Date(),
                duration: currentRecordingDuration
            )
            recordings.append(recording)
            saveRecordings()
        }

        currentRecordingDuration = 0
        currentRecordingStartTime = nil
    }

    func deleteRecording(_ recording: Recording) {
        let path = getDocumentsDirectory().appendingPathComponent(recording.filename)
        try? FileManager.default.removeItem(at: path)

        recordings.removeAll { $0.id == recording.id }
        saveRecordings()
    }

    func getRecordingURL(for recording: Recording) -> URL {
        return getDocumentsDirectory().appendingPathComponent(recording.filename)
    }

    func updateRecording(_ recording: Recording) {
        if let index = recordings.firstIndex(where: { $0.id == recording.id }) {
            recordings[index] = recording
            saveRecordings()
        }
    }

    func playRecording(_ recording: Recording) {
        let url = getRecordingURL(for: recording)

        do {
            audioPlayer = try AVAudioPlayer(contentsOf: url)
            audioPlayer?.play()
        } catch {
            print("Failed to play recording: \(error)")
        }
    }

    func stopPlaying() {
        audioPlayer?.stop()
    }

    // MARK: - Persistence

    private func getDocumentsDirectory() -> URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
    }

    private func saveRecordings() {
        if let encoded = try? JSONEncoder().encode(recordings) {
            UserDefaults.standard.set(encoded, forKey: "recordings")
        }
    }

    private func loadRecordings() {
        if let data = UserDefaults.standard.data(forKey: "recordings"),
           let decoded = try? JSONDecoder().decode([Recording].self, from: data) {
            recordings = decoded
        }
    }
}

extension AudioRecorderManager: AVAudioRecorderDelegate {
    func audioRecorderDidFinishRecording(_ recorder: AVAudioRecorder, successfully flag: Bool) {
        if !flag {
            print("Recording failed")
        }
    }
}

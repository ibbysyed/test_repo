import Foundation

struct Recording: Identifiable, Codable {
    let id: UUID
    let filename: String
    let date: Date
    var transcription: String?
    var uploadedToSnowflake: Bool
    var duration: TimeInterval

    init(id: UUID = UUID(), filename: String, date: Date = Date(), transcription: String? = nil, uploadedToSnowflake: Bool = false, duration: TimeInterval = 0) {
        self.id = id
        self.filename = filename
        self.date = date
        self.transcription = transcription
        self.uploadedToSnowflake = uploadedToSnowflake
        self.duration = duration
    }
}

import SwiftUI

struct SettingsView: View {
    @StateObject private var viewModel = SettingsViewModel()
    @Environment(\.dismiss) var dismiss

    var body: some View {
        NavigationView {
            Form {
                // OpenAI Section
                Section {
                    SecureField("API Key", text: $viewModel.openAIAPIKey)
                        .autocapitalization(.none)
                        .autocorrectionDisabled()

                    HStack {
                        Image(systemName: viewModel.isOpenAIConfigured ? "checkmark.circle.fill" : "xmark.circle.fill")
                            .foregroundColor(viewModel.isOpenAIConfigured ? .green : .red)
                        Text(viewModel.isOpenAIConfigured ? "Configured" : "Not Configured")
                            .foregroundColor(.secondary)
                            .font(.caption)
                    }
                } header: {
                    Label("OpenAI Configuration", systemImage: "brain")
                } footer: {
                    Text("Get your API key from platform.openai.com")
                }

                // Snowflake Section
                Section {
                    TextField("Account Identifier", text: $viewModel.snowflakeAccount)
                        .autocapitalization(.none)
                        .autocorrectionDisabled()

                    TextField("Username", text: $viewModel.snowflakeUser)
                        .autocapitalization(.none)
                        .autocorrectionDisabled()

                    SecureField("Password", text: $viewModel.snowflakePassword)

                    TextField("Database", text: $viewModel.snowflakeDatabase)
                        .autocapitalization(.none)

                    TextField("Schema", text: $viewModel.snowflakeSchema)
                        .autocapitalization(.none)

                    TextField("Warehouse", text: $viewModel.snowflakeWarehouse)
                        .autocapitalization(.none)

                    TextField("Table Name", text: $viewModel.snowflakeTable)
                        .autocapitalization(.none)

                    HStack {
                        Image(systemName: viewModel.isSnowflakeConfigured ? "checkmark.circle.fill" : "xmark.circle.fill")
                            .foregroundColor(viewModel.isSnowflakeConfigured ? .green : .red)
                        Text(viewModel.isSnowflakeConfigured ? "Configured" : "Not Configured")
                            .foregroundColor(.secondary)
                            .font(.caption)
                    }
                } header: {
                    Label("Snowflake Configuration", systemImage: "cloud.fill")
                } footer: {
                    Text("Account format: account_name.region (e.g., abc12345.us-east-1)")
                }

                // Actions Section
                Section {
                    Button(action: {
                        viewModel.saveSettings()
                    }) {
                        HStack {
                            Image(systemName: "checkmark.circle.fill")
                            Text("Save Settings")
                        }
                        .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(!viewModel.isFullyConfigured)

                    Button(role: .destructive, action: {
                        viewModel.clearSettings()
                    }) {
                        HStack {
                            Image(systemName: "trash")
                            Text("Clear All Settings")
                        }
                        .frame(maxWidth: .infinity)
                    }
                } footer: {
                    if !viewModel.isFullyConfigured {
                        Text("Fill in all required fields to save")
                            .foregroundColor(.orange)
                    }
                }

                // Information Section
                Section {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Security")
                            .font(.headline)
                        Text("Your API keys and credentials are securely stored in the iOS Keychain and never leave your device.")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                } header: {
                    Label("Information", systemImage: "info.circle")
                }
            }
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
            .alert("Settings Saved", isPresented: $viewModel.showingSaveConfirmation) {
                Button("OK") {
                    dismiss()
                }
            } message: {
                Text("Your configuration has been saved successfully.")
            }
            .alert("Error", isPresented: $viewModel.showingError) {
                Button("OK") { }
            } message: {
                Text(viewModel.saveError ?? "An unknown error occurred")
            }
        }
    }
}

#Preview {
    SettingsView()
}

const { REST, Routes } = require("discord.js");
const { token, clientId } = require("./config.json");
const fs = require("fs");
const path = require("path");

const commands = [];

// Load all command files from the commands folder
const commandsPath = path.join(__dirname, "commands");
const commandFiles = fs
  .readdirSync(commandsPath)
  .filter((file) => file.endsWith(".js"));

for (const file of commandFiles) {
  const filePath = path.join(commandsPath, file);
  const command = require(filePath);
  
  if ("data" in command && "execute" in command) {
    commands.push(command.data.toJSON());
    console.log(`✅ Loaded command: ${command.data.name}`);
  } else {
    console.log(
      `⚠️  The command at ${filePath} is missing "data" or "execute" property.`
    );
  }
}

// Deploy commands to Discord
const rest = new REST().setToken(token);

(async () => {
  try {
    console.log(
      `🚀 Started refreshing ${commands.length} application (/) commands.`
    );

    // Register commands globally (takes up to 1 hour to propagate)
    // For faster testing, you can use guild-specific commands instead
    const data = await rest.put(Routes.applicationCommands(clientId), {
      body: commands,
    });

    console.log(
      `✅ Successfully reloaded ${data.length} application (/) commands.`
    );
  } catch (error) {
    console.error("❌ Error deploying commands:", error);
  }
})();

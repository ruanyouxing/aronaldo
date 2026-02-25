const { Client, Collection, Events, GatewayIntentBits } = require("discord.js");
require("dotenv").config();
const token = process.env.token;
const fs = require("fs");
const path = require("path");

const client = new Client({
  intents: [GatewayIntentBits.Guilds],
});

// Load commands
client.commands = new Collection();
const commandsPath = path.join(__dirname, "commands");
const commandFiles = fs
  .readdirSync(commandsPath)
  .filter((file) => file.endsWith(".js"));

for (const file of commandFiles) {
  const filePath = path.join(commandsPath, file);
  const command = require(filePath);

  if ("data" in command && "execute" in command) {
    client.commands.set(command.data.name, command);
    console.log(`✅ Loaded command: ${command.data.name}`);
  } else {
    console.log(
      `⚠️  The command at ${filePath} is missing "data" or "execute" property.`,
    );
  }
}

// Bot ready event
client.once(Events.ClientReady, (readyClient) => {
  console.log(`✅ Ready! Logged in as ${readyClient.user.tag}`);
  console.log(`📊 Loaded ${client.commands.size} command(s)`);
});

// Handle slash command interactions
client.on(Events.InteractionCreate, async (interaction) => {
  if (!interaction.isChatInputCommand()) return;

  const command = client.commands.get(interaction.commandName);

  if (!command) {
    console.error(`❌ Không tìm thấy ${interaction.commandName}.`);
    return;
  }

  try {
    await command.execute(interaction);
  } catch (error) {
    console.error(`❌ Error executing ${interaction.commandName}:`, error);

    const errorMessage = {
      content: "❌ Có lỗi xảy ra khi thực thi câu lệnh!",
      ephemeral: true,
    };

    if (interaction.replied || interaction.deferred) {
      await interaction.followUp(errorMessage);
    } else {
      await interaction.reply(errorMessage);
    }
  }
});

client.login(token);

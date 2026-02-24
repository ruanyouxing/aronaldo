const { Client, Events, GatewayIntentBits, PermissionFlagsBits } = require("discord.js");
const { token } = require("./config.json");

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
  ],
});

// Configuration - you can modify these
const COMMAND_PREFIX = "/";
const SHARE_COMMAND = "sharelink";
const PRIVILEGED_ROLE_NAME = "chủ pếch";

client.once(Events.ClientReady, (readyClient) => {
  console.log(`Ready! Logged in as ${readyClient.user.tag}`);
});

// Handle messages
client.on(Events.MessageCreate, async (message) => {
  // Ignore bot messages
  if (message.author.bot) return;

  // Check if message starts with command prefix
  if (!message.content.startsWith(COMMAND_PREFIX)) return;

  const args = message.content.slice(COMMAND_PREFIX.length).trim().split(/\s+/);
  const command = args.shift().toLowerCase();

  // Handle the share command
  if (command === SHARE_COMMAND) {
    // Check permissions: Admin or specific privileged role
    const isAdmin = message.member.permissions.has(PermissionFlagsBits.Administrator);
    const hasPrivilegedRole = message.member.roles.cache.some(
      (role) => role.name === PRIVILEGED_ROLE_NAME
    );

    if (!isAdmin && !hasPrivilegedRole) {
      return message.reply(
        "❌ You don't have permission to use this command. You need Administrator permission or the " +
          PRIVILEGED_ROLE_NAME +
          " role."
      );
    }

    // Parse arguments: !share <link> <@role>
    if (args.length < 2) {
      return message.reply(
        "❌ Usage: `!sharelink <link> <@role>`\n" +
          "Example: `!sharelink https://example.com @sếch thủ`"
      );
    }

    let link = args[0];
    const roleMention = args[1];

    // Add https:// if no protocol is specified
    if (!link.match(/^https?:\/\//i)) {
      link = "https://" + link;
    }

    // Validate URL
    try {
      new URL(link);
    } catch (error) {
      return message.reply("❌ Invalid URL. Please provide a valid link.");
    }

    // Extract role from mention or find by name
    let role = null;
    if (roleMention.startsWith("<@&") && roleMention.endsWith(">")) {
      // It's a role mention
      const roleId = roleMention.slice(3, -1);
      role = message.guild.roles.cache.get(roleId);
    } else {
      // Try to find role by name (removing @ if present)
      const roleName = roleMention.replace(/^@/, "");
      role = message.guild.roles.cache.find((r) => r.name === roleName);
    }

    if (!role) {
      return message.reply(
        "❌ Role not found. Please mention a valid role or use the role name."
      );
    }

    // Delete the original command message (optional)
    try {
      await message.delete();
    } catch (error) {
      console.log("Could not delete command message:", error.message);
    }

    // Send the link with role ping
    try {
      await message.channel.send(`${role} ${link}`);
    } catch (error) {
      console.error("Error sending message:", error);
      return message.reply("❌ Failed to send the message.");
    }
  }
});

client.login(token);

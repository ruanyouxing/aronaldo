const { SlashCommandBuilder, PermissionFlagsBits } = require("discord.js");
const { COMMAND_CHANNEL, OUTPUT_CHANNEL } = require("../config/channels");
const { PRIVILEGED_ROLE } = require("../config/permissions");
const { validateUrl } = require("../utils/validators");
const { createAnnouncementEmbed } = require("../utils/embedBuilder");

module.exports = {
  data: new SlashCommandBuilder()
    .setName("thongbao")
    .setDescription("Post an announcement to the announcement channel")
    .addStringOption((option) =>
      option
        .setName("title")
        .setDescription("Main title of the announcement")
        .setRequired(true)
    )
    .addStringOption((option) =>
      option
        .setName("link1")
        .setDescription("First link (required)")
        .setRequired(true)
    )
    .addStringOption((option) =>
      option
        .setName("description")
        .setDescription("Description/details text")
        .setRequired(false)
    )
    .addStringOption((option) =>
      option
        .setName("link2")
        .setDescription("Second link (optional)")
        .setRequired(false)
    )
    .addStringOption((option) =>
      option
        .setName("link3")
        .setDescription("Third link (optional)")
        .setRequired(false)
    )
    .addStringOption((option) =>
      option
        .setName("cover")
        .setDescription("Cover image URL")
        .setRequired(false)
    )
    .addStringOption((option) =>
      option
        .setName("archive")
        .setDescription("Archive link (URL)")
        .setRequired(false)
    )
    .addAttachmentOption((option) =>
      option
        .setName("archive_file")
        .setDescription("Archive file attachment")
        .setRequired(false)
    )
    .addStringOption((option) =>
      option
        .setName("fanpage")
        .setDescription("Fanpage link")
        .setRequired(false)
    ),

  async execute(interaction) {
    // Check if command is used in the correct channel
    if (interaction.channel.name !== COMMAND_CHANNEL) {
      return interaction.reply({
        content: `❌ This command can only be used in #${COMMAND_CHANNEL}`,
        ephemeral: true,
      });
    }

    // Check permissions: Admin or privileged role
    const isAdmin = interaction.member.permissions.has(
      PermissionFlagsBits.Administrator
    );
    const hasPrivilegedRole = interaction.member.roles.cache.some(
      (role) => role.name === PRIVILEGED_ROLE
    );

    if (!isAdmin && !hasPrivilegedRole) {
      return interaction.reply({
        content: `❌ You don't have permission to use this command. You need Administrator permission or the "${PRIVILEGED_ROLE}" role.`,
        ephemeral: true,
      });
    }

    // Get all parameters
    const title = interaction.options.getString("title");
    const link1 = interaction.options.getString("link1");
    const description = interaction.options.getString("description");
    const link2 = interaction.options.getString("link2");
    const link3 = interaction.options.getString("link3");
    const cover = interaction.options.getString("cover");
    const archive = interaction.options.getString("archive");
    const archiveFile = interaction.options.getAttachment("archive_file");
    const fanpage = interaction.options.getString("fanpage");

    // Prioritize archive_file over archive URL
    const archiveUrl = archiveFile ? archiveFile.url : archive;

    // Validate all URLs (skip validation for attachment URLs from Discord CDN)
    const urlsToValidate = [
      { name: "link1", url: link1, required: true },
      { name: "link2", url: link2, required: false },
      { name: "link3", url: link3, required: false },
      { name: "cover", url: cover, required: false },
      { name: "archive", url: archiveFile ? null : archiveUrl, required: false }, // Skip if it's a file attachment
      { name: "fanpage", url: fanpage, required: false },
    ];

    const validatedUrls = {};
    for (const { name, url, required } of urlsToValidate) {
      if (!url && !required) continue;
      
      if (!url && required) {
        return interaction.reply({
          content: `❌ ${name} is required`,
          ephemeral: true,
        });
      }

      const result = validateUrl(url);
      if (!result.valid) {
        return interaction.reply({
          content: `❌ Invalid URL for ${name}: ${result.error}`,
          ephemeral: true,
        });
      }
      validatedUrls[name] = result.url;
    }

    // Find the output channel
    const outputChannel = interaction.guild.channels.cache.find(
      (ch) => ch.name === OUTPUT_CHANNEL
    );

    if (!outputChannel) {
      return interaction.reply({
        content: `❌ Could not find the #${OUTPUT_CHANNEL} channel`,
        ephemeral: true,
      });
    }

    // Create the embedded announcement
    const embed = createAnnouncementEmbed({
      title,
      description,
      link1: validatedUrls.link1,
      link2: validatedUrls.link2,
      link3: validatedUrls.link3,
      cover: validatedUrls.cover,
      archive: archiveFile ? archiveFile.url : validatedUrls.archive,
      fanpage: validatedUrls.fanpage,
    });

    // Send the announcement
    try {
      await outputChannel.send({ embeds: [embed] });
      
      // Confirm success to the user (ephemeral)
      await interaction.reply({
        content: `✅ Announcement posted successfully to #${OUTPUT_CHANNEL}`,
        ephemeral: true,
      });
    } catch (error) {
      console.error("Error posting announcement:", error);
      await interaction.reply({
        content: "❌ Failed to post the announcement. Please try again.",
        ephemeral: true,
      });
    }
  },
};

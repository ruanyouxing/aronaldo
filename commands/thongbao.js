const { SlashCommandBuilder, PermissionFlagsBits } = require("discord.js");
const { fanpageURL } = require("../config.json");
const {
  COMMAND_CHANNEL_ID,
  ANNOUNCEMENT_CHANNEL_ID,
  ROLE_ID,
} = require("../config.json");
const { validateUrl } = require("../utils/validators");
const { createAnnouncementEmbed } = require("../utils/embedBuilder");

module.exports = {
  data: new SlashCommandBuilder()
    .setName("thongbao")
    .setDescription("Đăng thông báo cho các sếch thủ")
    .addStringOption((option) =>
      option
        .setName("title")
        .setDescription("Tiêu đề")
        .setRequired(true),
    )
    .addStringOption((option) =>
      option
        .setName("link1")
        .setDescription("Link đọc số 1 (bắt buộc)")
        .setRequired(true),
    )
    .addStringOption((option) =>
      option
        .setName("ping")
        .setDescription("Có ping ai không?")
        .setRequired(false),
    )
    .addStringOption((option) =>
      option
        .setName("description")
        .setDescription("Nội dung/mô tả")
        .setRequired(false),
    )
    .addStringOption((option) =>
      option
        .setName("link2")
        .setDescription("Link đọc thứ hai (không bắt buộc)")
        .setRequired(false),
    )
    .addStringOption((option) =>
      option
        .setName("link3")
        .setDescription("Link đọc thứ ba (không bắt buộc)")
        .setRequired(false),
    )
    .addAttachmentOption((option) =>
      option
        .setName("cover")
        .setDescription("File ảnh bìa")
        .setRequired(false),
    )
    .addStringOption((option) =>
      option
        .setName("archive")
        .setDescription("Link archive Google Drive")
        .setRequired(false),
    )
    .addAttachmentOption((option) =>
      option
        .setName("archive_file")
        .setDescription("Hoặc file rar")
        .setRequired(false),
    ),

  async execute(interaction) {
    // Check permissions: Admin or privileged role
    const isAdmin = interaction.member.permissions.has(
      PermissionFlagsBits.Administrator,
    );
    const hasPrivilegedRole = interaction.member.roles.cache.some(
      (role) => role.id === ROLE_ID,
    );

    if (!isAdmin && !hasPrivilegedRole) {
      return interaction.reply({
        content: `❌ Bạn không có quyền sử dụng câu lệnh này. Bạn phải là chủ pếch hoặc <@&${ROLE_ID}>.`,
        ephemeral: true,
      });
    }
    // Check if command is used in the correct channel
    if (interaction.channel.id !== COMMAND_CHANNEL_ID) {
      return interaction.reply({
        content: `❌ Bạn chỉ có thể thông báo từ kênh <#${COMMAND_CHANNEL_ID}>`,
        ephemeral: true,
      });
    }

    // Get all parameters
    const title = interaction.options.getString("title");
    const link1 = interaction.options.getString("link1");
    const description = interaction.options.getString("description");
    const link2 = interaction.options.getString("link2");
    const link3 = interaction.options.getString("link3");
    const coverAttachment = interaction.options.getAttachment("cover");
    const ping = interaction.options.getString("ping");
    // if (coverAttachment) {
    //   if (
    //     !coverAttachment.contentType ||
    //     !coverAttachment.contentType.startsWith("image/")
    //   ) {
    //     return interaction.reply({
    //       content: "Invalid cover image",
    //       ephemeral: true,
    //     });
    //   }
    // }
    const archive = interaction.options.getString("archive");
    const archiveFile = interaction.options.getAttachment("archive_file");
    const fanpage = fanpageURL;

    // Prioritize archive_file over archive URL
    const archiveUrl = archiveFile ? archiveFile.url : archive;

    // Validate all URLs (skip validation for attachment URLs from Discord CDN)
    const urlsToValidate = [
      { name: "link1", url: link1, required: true },
      { name: "link2", url: link2, required: false },
      { name: "link3", url: link3, required: false },
      {
        name: "archive",
        url: archiveFile ? null : archiveUrl,
        required: false,
      }, // Skip if it's a file attachment
      { name: "fanpage", url: fanpage, required: false },
    ];

    const validatedUrls = {};
    for (const { name, url, required } of urlsToValidate) {
      if (!url && !required) continue;

      if (!url && required) {
        return interaction.reply({
          content: `❌ Cần phải có ${name}`,
          ephemeral: true,
        });
      }

      const result = validateUrl(url);
      if (!result.valid) {
        return interaction.reply({
          content: `❌ URL không hợp lệ ${name}: ${result.error}`,
          ephemeral: true,
        });
      }
      validatedUrls[name] = result.url;
    }

    // Find the output channel
    const outputChannel = interaction.guild.channels.cache.find(
      (ch) => ch.id === ANNOUNCEMENT_CHANNEL_ID,
    );

    if (!outputChannel) {
      return interaction.reply({
        content: `❌ Không tìm thấy kênh <#${ANNOUNCEMENT_CHANNEL_ID}> channel`,
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
      cover: coverAttachment ? coverAttachment.url : null,
      archive: archiveFile ? archiveFile.url : validatedUrls.archive,
      fanpage: validatedUrls.fanpage,
    });

    // Send the announcement
    try {
      await outputChannel.send({
        content: ping ? ping : null,
        embeds: [embed],
      });

      // Confirm success to the user (ephemeral)
      await interaction.reply({
        content: `✅ Thông báo đã được đăng thành công lên kênh <#${ANNOUNCEMENT_CHANNEL_ID}>!`,
        ephemeral: true,
      });
    } catch (error) {
      console.error("Error posting announcement:", error);
      await interaction.reply({
        content: "❌ Đăng thông báo thất bại. Xin hãy thử lại.",
        ephemeral: true,
      });
    }
  },
};

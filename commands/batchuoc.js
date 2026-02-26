const { SlashCommandBuilder, PermissionFlagsBits } = require("discord.js");
const {
  COMMAND_CHANNEL_ID,
  ANNOUNCEMENT_CHANNEL_ID,
  ROLE_ID,
} = require("../config.json");

module.exports = {
  data: new SlashCommandBuilder()
    .setName("batchuoc")
    .setDescription("Rô vẹt")
    .addStringOption((option) =>
      option.setName("text").setDescription("Tin nhắn gì đó").setRequired(false)
    )
    .addAttachmentOption((option) =>
      option
        .setName("attachment")
        .setDescription("File đính kèm")
        .setRequired(false)
    ),

  async execute(interaction) {
    const isAdmin = interaction.member.permissions.has(
      PermissionFlagsBits.Administrator
    );
    const hasPrivilegedRole = interaction.member.roles.cache.some(
      (role) => role.id === ROLE_ID
    );

    if (!isAdmin && !hasPrivilegedRole) {
      return interaction.reply({
        content: `❌ Bạn không có quyền sử dụng câu lệnh này. Bạn phải là chủ pếch hoặc <@&${ROLE_ID}>.`,
        ephemeral: true,
      });
    }
    if (interaction.channel.id !== COMMAND_CHANNEL_ID) {
      return interaction.reply({
        content: `❌ Bạn chỉ có thể thông báo từ kênh <#${COMMAND_CHANNEL_ID}>`,
        ephemeral: true,
      });
    }
    const text = interaction.options.getString("text");
    const attachment = interaction.options.getAttachment("attachment");

    // 1. Prevent the bot from crashing if the user provides absolutely nothing
    if (!text && !attachment) {
      return interaction.reply({
        content: "❌ quắt đờ phắc, có gì đâu mà nhép",
        ephemeral: true,
      });
    }

    // 2. Build the message payload dynamically
    const payload = {};

    if (text) {
      payload.content = text;
    }

    // 3. Handle the attachment by passing it into Discord's 'files' array
    if (attachment) {
      payload.files = [
        {
          attachment: attachment.url,
          name: attachment.name, // Keeps the original filename
        },
      ];
    }
    const outputChannel = interaction.guild.channels.cache.find(
      (ch) => ch.id === ANNOUNCEMENT_CHANNEL_ID
    );
    if (!outputChannel) {
      return interaction.reply({
        content: `❌ Không tìm thấy kênh <#${ANNOUNCEMENT_CHANNEL_ID}>`,
        ephemeral: true,
      });
    }
    try {
      await outputChannel.send(payload);

      // 5. Silently complete the interaction so Discord doesn't show an error
      await interaction.reply({
        content: `✅ Đã nhép thành công trên kênh <#${ANNOUNCEMENT_CHANNEL_ID}>!`,
        ephemeral: true,
      });
    } catch (error) {
      console.error("Mimic error:", error);

      // Safety net in case the bot lacks permissions to send messages or files
      if (!interaction.replied) {
        await interaction.reply({
          content: "❌ Lỗi",
          ephemeral: true,
        });
      }
    }
  },
};

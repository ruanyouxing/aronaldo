const { EmbedBuilder } = require("discord.js");

/**
 * Creates an embedded announcement message
 * @param {Object} options - The announcement options
 * @param {string} options.title - Main title
 * @param {string} options.description - Description text
 * @param {string} options.link1 - First link (required)
 * @param {string} options.link2 - Second link
 * @param {string} options.link3 - Third link
 * @param {string} options.cover - Cover image attachment
 * @param {string} options.archive - Archive link
 * @param {string} options.fanpage - Fanpage link
 * @returns {EmbedBuilder} - The embedded message
 */

const { translationTeamURL, fanpageURL } = require("../config.json");
function createAnnouncementEmbed(options) {
  const { title, description, link1, link2, link3, cover, archive } = options;

  const embed = new EmbedBuilder()
    .setColor("#ba30ff") // Discord blurple color
    .setTitle(title)
    .setTimestamp();

  // Add description if provided
  if (description) {
    embed.setDescription(description);
  }

  // Add cover image if provided
  if (cover) {
    embed.setImage(cover);
  }

  // Build links section
  let linksText = "";
  if (link1) {
    linksText += `🔗 [Vi-h](${link1})\n`;
  }
  if (link2) {
    linksText += `🔗 [Mimi](${link2})\n`;
  }
  if (link3) {
    linksText += `🔗 [Vinahentai](${link3})\n`;
  }

  if (linksText) {
    embed.addFields({
      name: "📎 Link",
      value: linksText,
      inline: false,
    });
  }

  // Add archive and fanpage as inline fields
  if (archive) {
    embed.addFields({
      name: "📦 Archive",
      value: `[Xem archive](${archive})`,
      inline: true,
    });
  }
  embed.addFields({
    name: "📚 Truyện khác",
    value: `[Nhóm chúng tôi trên vi-h](${translationTeamURL})`,
    inline: false,
  });
  embed.addFields({
    name: "👥 Liên hệ",
    value: `[Phan pếch chúng tôi](${fanpageURL})`,
    inline: true,
  });

  return embed;
}

module.exports = {
  createAnnouncementEmbed,
};

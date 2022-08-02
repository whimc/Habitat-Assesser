package edu.whimc.photographer;

import org.bukkit.ChatColor;
import org.bukkit.command.CommandSender;

public final class Utils {

    public static void msg(CommandSender sender, String... messages) {
        for (String message : messages) {
            sender.sendMessage(color(message));
        }
    }

    public static String color(String str) {
        return ChatColor.translateAlternateColorCodes('&', str);
    }

}

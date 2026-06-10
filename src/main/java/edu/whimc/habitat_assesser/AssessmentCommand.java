package edu.whimc.habitat_assesser;

import com.corundumstudio.socketio.SocketIOClient;
import edu.whimc.habitat_assesser.HabitatAssesser;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import edu.whimc.overworld_agent.dialoguetemplate.events.BuildAssessEvent;
import org.bukkit.Bukkit;
import org.bukkit.ChatColor;
import org.bukkit.command.Command;
import org.bukkit.command.CommandExecutor;
import org.bukkit.command.CommandSender;
import org.bukkit.command.TabCompleter;
import org.bukkit.entity.Player;

public class AssessmentCommand implements CommandExecutor, TabCompleter {

    private final HabitatAssesser plugin;

    public AssessmentCommand(HabitatAssesser plugin) {
        this.plugin = plugin;
    }

    @Override
    public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {
        if (!sender.hasPermission("whimc-habitat-assessment.admin")) {
            sender.sendMessage(ChatColor.RED + "No permission!");
            return true;
        }

        if (args.length == 0) {
            sendUsage(sender);
            return true;
        }

        String subCmd = args[0];

        if (subCmd.equalsIgnoreCase("clients")) {
            Utils.msg(sender, "&b&lClients:");
            for (SocketIOClient client : this.plugin.getSocketServer().getAllClients()) {
                Utils.msg(sender, "> &b" + client.get("uuid"));
                Utils.msg(sender, "|  IP: &b" + client.getRemoteAddress());
            }
            return true;
        }

        if (subCmd.equalsIgnoreCase("queue-list")) {
            Utils.msg(sender, "&b&lQueued assessments:");
            for (BuildAssessEvent event : this.plugin.getAssessmentQueue()) {
                Utils.msg(sender, "Assessment ID: " + event.getId());
            }
            return true;
        }

        if (subCmd.equalsIgnoreCase("queue-clear")) {
            int numCleared = this.plugin.getAssessmentQueue().size();
            this.plugin.getAssessmentQueue().clear();
            Utils.msg(sender, "&aCleared " + numCleared + " queued habitat assessments");
            return true;
        }

        if (subCmd.equalsIgnoreCase("queue-remove")) {
            if (args.length < 2) {
                Utils.msg(sender, "&o/habitats queue-remove <id>");
                return true;
            }

            String assessment_id = args[1];
            boolean removed = this.plugin.getAssessmentQueue().removeIf(assessment -> String.valueOf(assessment.getId()).equals(assessment_id));
            if (removed) {
                Utils.msg(sender, "&aRemoved assessment " + assessment_id + " from the queue");
            } else {
                Utils.msg(sender, "&cNo assessment with id " + assessment_id + " found in queue");
            }

            return true;
        }

        if (args.length < 2) {
            return true;
        }

        UUID uuid;
        try {
            uuid = UUID.fromString(args[1]);
        } catch (IllegalArgumentException exc) {
            sender.sendMessage("Invalid UUID");
            return true;
        }
        Optional<SocketIOClient> clientOpt = this.plugin.getClient(uuid);

        if (!clientOpt.isPresent()) {
            sender.sendMessage("Client not found");
            return true;
        }

        SocketIOClient client = clientOpt.get();

        if (subCmd.equalsIgnoreCase("disconnect")) {
            sender.sendMessage("Disconnecting " + client.getRemoteAddress() + ": " + client.get("uuid"));
            client.disconnect();
            return true;
        }

        sendUsage(sender);
        return true;
    }

    private void sendUsage(CommandSender sender) {
        Utils.msg(sender,
                "&e/habitats &6clients",
                "&e/habitats &6queue-list",
                "&e/habitats &6queue-clear",
                "&e/habitats &6queue-remove &7<id>",
                "&e/habitats &6disconnect &7<uuid>"
        );
    }

    @Override
    public List<String> onTabComplete(CommandSender sender, Command command, String alias, String[] args) {
        if (args.length <= 1) {
            return Stream.of(
                            "clients",
                            "queue-list",
                            "queue-clear",
                            "queue-remove",
                            "disconnect"
                    ).filter(arg -> arg.startsWith(args[0].toLowerCase()))
                    .collect(Collectors.toList());
        }

        return this.plugin.getSocketServer().getAllClients().stream()
                .map(client -> client.get("uuid").toString())
                .collect(Collectors.toList());
    }

}

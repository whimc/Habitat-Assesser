package edu.whimc.photographer.socket;

public class AssessmentResponse {

    private String user;
    private int id;
    private String feedback;

    public AssessmentResponse () {
        super();
    }

    public AssessmentResponse(int interactionId, String playerName, String feedback) {
        this.user = playerName;
        this.id = interactionId;
        this.feedback = feedback;
    }


    public String getUser() {
        return user;
    }

    public int getId() {
        return id;
    }

    public String getFeedback(){return feedback;}

}
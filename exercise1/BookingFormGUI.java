import javax.swing.*;
import javax.swing.border.EmptyBorder;
import java.awt.*;
import java.io.IOException;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;

public class BookingFormGUI {
    private JFrame frame;
    private JTextField nameField;
    private JTextField surnameField;
    private JTextField emailField;
    private JComboBox<String> roomTypeBox;
    private JSpinner guestsSpinner;
    private JSpinner arrivalDateSpinner;
    private JSpinner arrivalTimeSpinner;
    private JTextField departureField;
    private JRadioButton pickupYes;
    private JRadioButton pickupNo;
    private JTextArea requestsArea;

 public BookingFormGUI() {
        frame = new JFrame("Hotel Booking");
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setSize(600, 600);

        JPanel panel = new JPanel(new GridBagLayout());
        panel.setBorder(new EmptyBorder(20, 20, 20, 20));
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(10, 10, 10, 10);
        gbc.fill = GridBagConstraints.HORIZONTAL;
        gbc.anchor = GridBagConstraints.WEST;

        int y = 0;
        gbc.gridx = 0; gbc.gridy = y;
        panel.add(new JLabel("First Name:"), gbc);
        gbc.gridx = 1;
        nameField = new JTextField();
        panel.add(nameField, gbc);
        gbc.gridx = 2;
        panel.add(new JLabel("Last Name:"), gbc);
        gbc.gridx = 3;
        surnameField = new JTextField();
        panel.add(surnameField, gbc);
        y++;

        gbc.gridx = 0; gbc.gridy = y;
        panel.add(new JLabel("E-mail:"), gbc);
        gbc.gridx = 1; gbc.gridwidth = 3;
        emailField = new JTextField();
        emailField.setToolTipText("e.g., name@example.com");
        panel.add(emailField, gbc);
        gbc.gridwidth = 1;
        y++;

        gbc.gridx = 0; gbc.gridy = y;
        panel.add(new JLabel("Room Type:"), gbc);
        gbc.gridx = 1;
        roomTypeBox = new JComboBox<>(new String[]{"single", "double", "suite"});
        roomTypeBox.setSelectedIndex(-1);
        panel.add(roomTypeBox, gbc);
        gbc.gridx = 2;
        panel.add(new JLabel("Number of Guests:"), gbc);
        gbc.gridx = 3;
        guestsSpinner = new JSpinner(new SpinnerNumberModel(1, 1, 20, 1));
        panel.add(guestsSpinner, gbc);
        y++;

        gbc.gridx = 0; gbc.gridy = y;
        panel.add(new JLabel("Arrival Date (yyyy-MM-dd):"), gbc);
        gbc.gridx = 1;
        arrivalDateSpinner = new JSpinner(new SpinnerDateModel());
        JSpinner.DateEditor dateEditor = new JSpinner.DateEditor(arrivalDateSpinner, "yyyy-MM-dd");
        arrivalDateSpinner.setEditor(dateEditor);
        panel.add(arrivalDateSpinner, gbc);
        gbc.gridx = 2;
        panel.add(new JLabel("Arrival Time (HH:mm):"), gbc);
        gbc.gridx = 3;
        arrivalTimeSpinner = new JSpinner(new SpinnerDateModel());
        JSpinner.DateEditor timeEditor = new JSpinner.DateEditor(arrivalTimeSpinner, "HH:mm");
        arrivalTimeSpinner.setEditor(timeEditor);
        panel.add(arrivalTimeSpinner, gbc);
        y++;

        gbc.gridx = 0; gbc.gridy = y;
        panel.add(new JLabel("Departure Date:"), gbc);
        gbc.gridx = 1; gbc.gridwidth = 3;
        departureField = new JTextField();
        departureField.setToolTipText("YYYY-MM-DD or DD/MM/YYYY or Month DD, YYYY");
        panel.add(departureField, gbc);
        gbc.gridwidth = 1;
        y++;

        gbc.gridx = 0; gbc.gridy = y;
        panel.add(new JLabel("Free Pickup?"), gbc);
        gbc.gridx = 1;
        pickupYes = new JRadioButton("Yes, pick me up");
        pickupNo = new JRadioButton("No, I'll arrange my own transport");
        ButtonGroup group = new ButtonGroup();
        group.add(pickupYes);
        group.add(pickupNo);
        pickupNo.setSelected(true);
        JPanel pickPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 10, 0));
        pickPanel.add(pickupYes); pickPanel.add(pickupNo);
        panel.add(pickPanel, gbc);
        y++;

        gbc.gridx = 0; gbc.gridy = y; gbc.anchor = GridBagConstraints.NORTHWEST;
        panel.add(new JLabel("Special Requests:"), gbc);
        gbc.gridx = 1; gbc.gridwidth = 3;
        requestsArea = new JTextArea(5, 30);
        panel.add(new JScrollPane(requestsArea), gbc);
        gbc.gridwidth = 1;
        y++;

        gbc.gridx = 3; gbc.gridy = y; gbc.anchor = GridBagConstraints.EAST;
        JButton submit = new JButton("Submit");
        submit.addActionListener(e -> handleSubmit());
        panel.add(submit, gbc);

        frame.add(panel);
        frame.setLocationRelativeTo(null);
        frame.setVisible(true);
    }
    
  private void handleSubmit() {
  
    String departureStr = departureField.getText().trim();

    Date arrDate = ((SpinnerDateModel) arrivalDateSpinner.getModel()).getDate();
    Date arrTime = ((SpinnerDateModel) arrivalTimeSpinner.getModel()).getDate();
    LocalDateTime arrival = LocalDateTime.parse(
        new SimpleDateFormat("yyyy-MM-dd").format(arrDate) + "T" +
        new SimpleDateFormat("HH:mm").format(arrTime),
        DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm")
    );

    String input = String.join(";",
        nameField.getText().trim(),
        surnameField.getText().trim(),
        emailField.getText().trim(),
        (String) roomTypeBox.getSelectedItem(),
        guestsSpinner.getValue().toString(),
        arrival.format(DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm")),
        departureStr,
        String.valueOf(pickupYes.isSelected()),
        requestsArea.getText().trim()
    );
  

    try {
      System.out.println("DEBUG – raw booking input → [" + input + "]");
      System.out.println("  name      = '" + nameField.getText().trim()       + "'");
      System.out.println("  surname   = '" + surnameField.getText().trim()    + "'");
      System.out.println("  email   = '" + emailField.getText().trim()    + "'");
      System.out.println("  roomType  = '" + roomTypeBox.getSelectedItem()    + "'");
      System.out.println("  guests    = '" + guestsSpinner.getValue()         + "'");
      System.out.println("  arrival   = '" + arrival + "'");             
      System.out.println("  departure = '" + departureStr + "'");
      System.out.println("  freePickup = '" + pickupYes.isSelected() + "'");
      System.out.println("  requests  = '" + requestsArea.getText().trim() + "'");
      
      String filename;
      try {
        filename = BookingForm.processBooking(input);
      } catch (IOException ioe) {
            throw new RuntimeException(ioe);
      }
      JOptionPane.showMessageDialog(frame, "Booking Confirmed!\nSaved to " + filename, "Success", JOptionPane.INFORMATION_MESSAGE);
    } catch (IllegalArgumentException ex) {
      JOptionPane.showMessageDialog(frame, ex.getMessage(), "Error", JOptionPane.ERROR_MESSAGE);
    }
  }

  public static void main(String[] args) {
    SwingUtilities.invokeLater(BookingFormGUI::new);
  }
}



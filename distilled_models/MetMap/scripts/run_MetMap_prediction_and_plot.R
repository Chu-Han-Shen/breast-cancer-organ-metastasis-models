required_packages <- c("readr", "dplyr", "tibble", "ranger", "ggplot2")
missing_packages <- required_packages[!vapply(required_packages, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing_packages) > 0) stop("Please install: ", paste(missing_packages, collapse = ", "))

dir.create("results", showWarnings = FALSE)
dir.create("figures", showWarnings = FALSE)

metmap <- readr::read_csv("data/MetMap_input_and_phenotypes.csv", show_col_types = FALSE)
liver_bundle <- readRDS("models/MetMap_liver_RF_bundle.rds")
bone_bundle <- readRDS("models/MetMap_bone_RF_bundle.rds")

predict_bundle <- function(data, bundle) {
  missing_features <- setdiff(bundle$retained_features, colnames(data))
  if (length(missing_features) > 0) stop("Missing model features: ", paste(missing_features, collapse = ", "))
  x <- as.data.frame(lapply(data[, bundle$retained_features, drop = FALSE], function(z) suppressWarnings(as.numeric(as.character(z)))), check.names = FALSE)
  for (feature in bundle$retained_features) x[[feature]][is.na(x[[feature]])] <- bundle$impute_values[[feature]]
  predicted_rank_z <- predict(bundle$model, data = x)$predictions
  stats::pnorm(as.numeric(predicted_rank_z))
}

metmap$Liver_risk_score <- predict_bundle(metmap, liver_bundle)
metmap$Bone_risk_score <- predict_bundle(metmap, bone_bundle)

id_candidates <- c("ModelID", "CCLEName", "DepMap_ID", "cell_line")
id_col <- id_candidates[id_candidates %in% colnames(metmap)][1]
output_cols <- c(id_col, "Liver_risk_score", "Bone_risk_score", "mean.liver", "mean.bone")
output_cols <- output_cols[!is.na(output_cols) & output_cols %in% colnames(metmap)]
readr::write_csv(metmap[, output_cols, drop = FALSE], "results/MetMap_risk_scores.csv", na = "")

bootstrap_spearman <- function(score, potential, organ, B = 2000, seed = 42) {
  dat <- tibble::tibble(Risk_score = score, Organ_potential = potential) %>% dplyr::filter(stats::complete.cases(.))
  set.seed(seed)
  rho <- suppressWarnings(stats::cor(dat$Risk_score, dat$Organ_potential, method = "spearman"))
  p_value <- suppressWarnings(stats::cor.test(dat$Risk_score, dat$Organ_potential, method = "spearman", exact = FALSE)$p.value)
  boot_rho <- replicate(B, {
    index <- sample(seq_len(nrow(dat)), nrow(dat), replace = TRUE)
    suppressWarnings(stats::cor(dat$Risk_score[index], dat$Organ_potential[index], method = "spearman"))
  })
  boot_rho <- boot_rho[is.finite(boot_rho)]
  tibble::tibble(Organ = organ, N = nrow(dat), Rho = rho, CI_lower = as.numeric(stats::quantile(boot_rho, 0.025, na.rm = TRUE)), CI_upper = as.numeric(stats::quantile(boot_rho, 0.975, na.rm = TRUE)), P_value = p_value)
}

organ_result <- dplyr::bind_rows(
  bootstrap_spearman(metmap$Liver_risk_score, metmap$mean.liver, "Liver"),
  bootstrap_spearman(metmap$Bone_risk_score, metmap$mean.bone, "Bone")
) %>%
  dplyr::mutate(
    Organ = factor(Organ, levels = c("Bone", "Liver")),
    P_label = ifelse(P_value < 0.001, "P < 0.001", paste0("P = ", sprintf("%.3f", P_value))),
    Result_label = paste0("rho = ", sprintf("%.2f", Rho), " (", sprintf("%.2f", CI_lower), " to ", sprintf("%.2f", CI_upper), "), ", P_label)
  )

readr::write_csv(organ_result, "results/MetMap_correlation_results.csv", na = "")

text_x <- max(organ_result$CI_upper, na.rm = TRUE) + 0.15
p <- ggplot2::ggplot(organ_result, ggplot2::aes(x = Rho, y = Organ)) +
  ggplot2::geom_vline(xintercept = 0, linetype = 2, linewidth = 0.7, color = "grey55") +
  ggplot2::geom_segment(ggplot2::aes(x = CI_lower, xend = CI_upper, yend = Organ), linewidth = 1.1, color = "grey35") +
  ggplot2::geom_point(ggplot2::aes(fill = Organ), shape = 21, size = 4.5, stroke = 0.7, color = "white") +
  ggplot2::geom_text(ggplot2::aes(x = text_x, label = Result_label), hjust = 0, size = 4) +
  ggplot2::scale_fill_manual(values = c("Liver" = "#E64B35", "Bone" = "#9E9E9E")) +
  ggplot2::coord_cartesian(xlim = c(min(-0.45, min(organ_result$CI_lower, na.rm = TRUE) - 0.05), text_x + 0.75), clip = "off") +
  ggplot2::labs(x = "Spearman correlation coefficient", y = NULL) +
  ggplot2::theme_classic(base_size = 13) +
  ggplot2::theme(axis.title.x = ggplot2::element_text(face = "bold", size = 12), axis.text.x = ggplot2::element_text(color = "black", size = 10), axis.text.y = ggplot2::element_text(color = "black", size = 12, face = "bold"), legend.position = "none", plot.margin = ggplot2::margin(12, 190, 10, 12))

ggplot2::ggsave("figures/MetMap_liver_bone_correlation_forest.pdf", p, width = 8, height = 3.8)
ggplot2::ggsave("figures/MetMap_liver_bone_correlation_forest.png", p, width = 8, height = 3.8, dpi = 400)

liver_expected <- readr::read_csv("expected_results/MetMap_liver_predictions.csv", show_col_types = FALSE)
bone_expected <- readr::read_csv("expected_results/MetMap_bone_predictions.csv", show_col_types = FALSE)
liver_check <- isTRUE(all.equal(metmap$Liver_risk_score, liver_expected$liver_risk_score, tolerance = 1e-12))
bone_check <- isTRUE(all.equal(metmap$Bone_risk_score, bone_expected$bone_risk_score, tolerance = 1e-12))

cat("Liver prediction reproduced: ", liver_check, "\n", sep = "")
cat("Bone prediction reproduced: ", bone_check, "\n", sep = "")
print(organ_result)
print(p)
